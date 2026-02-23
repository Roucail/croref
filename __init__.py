import bpy
import numpy as np

# --- CONFIGURATION ---
PIXEL_CACHE = {}
PREFIX_NAME = "CR_"

def get_np_array(image):
    """Gère le cache et la conversion vers NumPy."""
    if not image: return None
    img_id = image.as_pointer()
    
    if img_id not in PIXEL_CACHE:
        # Note: Cette opération peut prendre 0.5s sur de très grosses images
        w, h = image.size
        arr = np.array(image.pixels).reshape((h, w, 4))
        PIXEL_CACHE[img_id] = arr
        print(f"[Crop Tool] Cache créé : {image.name}")
    
    return PIXEL_CACHE[img_id]

def reset_crop_settings(props):
    """Réinitialise les réglages sans vider le cache global."""
    props.crop_x = 100.0
    props.crop_y = 100.0
    props.pos_x = 50.0
    props.pos_y = 50.0

# --- HANDLER DE SYNCHRONISATION ---
@bpy.app.handlers.persistent
def sync_empty_source_handler(scene):
    """Détecte les changements d'image via l'interface standard de Blender."""
    obj = bpy.context.object
    if not obj or obj.type != 'EMPTY' or obj.empty_display_type != 'IMAGE':
        return

    props = obj.simple_crop
    current_data = obj.data

    if not current_data:
        return

    # SÉCURITÉ : On n'autorise la synchro QUE si l'image n'est PAS un crop de notre add-on
    if not current_data.name.startswith(PREFIX_NAME):
        if props.source_image != current_data:
            props.source_image = current_data
            reset_crop_settings(props)
            # On ne vide pas PIXEL_CACHE.clear() ici pour garder les autres images en mémoire
            print(f"[Crop Tool] Source mise à jour pour {obj.name} -> {current_data.name}")

# --- LOGIQUE DE CROP ---
def crop_image_logic(context):
    obj = context.object
    props = obj.simple_crop
    orig_img = props.source_image
    
    if not orig_img: return

    # 1. Récupération des pixels (via cache)
    pixels_np = get_np_array(orig_img)
    if pixels_np is None: return
    src_h, src_w, _ = pixels_np.shape
    
    # 2. Calcul des dimensions
    crop_w = max(1, int(src_w * (props.crop_x / 100.0)))
    crop_h = max(1, int(src_h * (props.crop_y / 100.0)))
    
    start_x = int((src_w - crop_w) * (props.pos_x / 100.0))
    start_y = int((src_h - crop_h) * (props.pos_y / 100.0))
    
    # 3. Nommage unique (on nettoie le nom de l'image pour éviter CR_CR_...)
    clean_img_name = orig_img.name
    if clean_img_name.startswith(PREFIX_NAME+obj.name+"_"):
        clean_img_name = clean_img_name.replace(PREFIX_NAME+obj.name+"_", "")
        
    new_name = f"{PREFIX_NAME}{obj.name}_{clean_img_name}"[:63]
    
    # 4. Gestion du bloc Image
    if new_name in bpy.data.images:
        new_img = bpy.data.images[new_name]
        if new_img.size[0] != crop_w or new_img.size[1] != crop_h:
            new_img.scale(crop_w, crop_h)
    else:
        new_img = bpy.data.images.new(new_name, width=crop_w, height=crop_h)

    # 5. Application des pixels
    cropped_array = pixels_np[start_y : start_y + crop_h, start_x : start_x + crop_w, :]
    new_img.pixels = cropped_array.flatten()

    # 6. Assignation (le handler ignorera cette étape grâce au préfixe CR_)
    obj.data = new_img
    
def update_crop_callback(self, context):
    """Callback pour la mise à jour dynamique."""
    # On vérifie que la source n'est pas elle-même un crop par erreur
    if self.source_image and not self.source_image.name.startswith(PREFIX_NAME):
        if self.auto_update:
            crop_image_logic(context)

# --- UI & PROPRIÉTÉS ---
class SimpleEmptyCropProps(bpy.types.PropertyGroup):
    # La source pointe vers l'image d'origine
    source_image: bpy.props.PointerProperty(
        type=bpy.types.Image, 
        name="Image Source",
        description="L'image originale non recadrée"
    )
    
    auto_update: bpy.props.BoolProperty(
        name="Auto", 
        description="Mise à jour en temps réel",
        default=True
    )
    
    crop_x: bpy.props.FloatProperty(name="Largeur %", default=100.0, min=1.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)
    crop_y: bpy.props.FloatProperty(name="Hauteur %", default=100.0, min=1.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)
    pos_x:  bpy.props.FloatProperty(name="Position X %", default=50.0, min=0.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)
    pos_y:  bpy.props.FloatProperty(name="Position Y %", default=50.0, min=0.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)

class OBJECT_OT_apply_crop(bpy.types.Operator):
    bl_idname = "empty.apply_crop"
    bl_label = "Recadrer maintenant"
    bl_description = "Force le calcul du recadrage"
    
    def execute(self, context):
        crop_image_logic(context)
        return {'FINISHED'}

class DATA_PT_empty_crop_ui(bpy.types.Panel):
    bl_label = "Crop de Référence"
    bl_space_type = 'PROPERTIES'; bl_region_type = 'WINDOW'; bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'EMPTY' and context.object.empty_display_type == 'IMAGE'

    def draw(self, layout):
        obj = bpy.context.object
        p = obj.simple_crop
        
        # Affichage de la source actuelle
        self.layout.prop(p, "source_image")
        
        row = self.layout.row(align=True)
        row.operator("empty.apply_crop")
        row.prop(p, "auto_update", text="Auto", toggle=True)
        
        col = self.layout.column(align=True)
        col.prop(p, "crop_x")
        col.prop(p, "crop_y")
        col.separator()
        col.prop(p, "pos_x")
        col.prop(p, "pos_y")

# --- REGISTRATION ---
_classes = (SimpleEmptyCropProps, OBJECT_OT_apply_crop, DATA_PT_empty_crop_ui)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.simple_crop = bpy.props.PointerProperty(type=SimpleEmptyCropProps)
    bpy.app.handlers.depsgraph_update_post.append(sync_empty_source_handler)

def unregister():
    if sync_empty_source_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(sync_empty_source_handler)
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Object.simple_crop
    PIXEL_CACHE.clear()

if __name__ == "__main__":
    register()

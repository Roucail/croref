import bpy
import numpy as np

# Cache global pour la rapidité
PIXEL_CACHE = {}

def get_np_array(image):
    """Gère le cache et la conversion lente vers NumPy."""
    if not image: return None
    
    # On utilise l'ID interne pour éviter les problèmes de renommage
    img_id = image.as_pointer()
    
    if img_id not in PIXEL_CACHE:
        # L'opération coûteuse n'est faite qu'une fois
        w, h = image.size
        arr = np.array(image.pixels).reshape((h, w, 4))
        PIXEL_CACHE[img_id] = arr
        print(f"[Crop Tool] Cache créé pour: {image.name}")
    
    return PIXEL_CACHE[img_id]

def reset_crop_settings(props, image):
    """Remet les curseurs à zéro."""
    props.crop_x = 100.0
    props.crop_y = 100.0
    props.pos_x = 50.0
    props.pos_y = 50.0
    # On vide le cache car l'image source a changé
    PIXEL_CACHE.clear()

# --- HANDLER DE SYNCHRONISATION ---
@bpy.app.handlers.persistent
def sync_empty_source_handler(scene):
    """Surveille si l'image de l'Empty a été changée via l'interface native."""
    obj = bpy.context.object
    if not obj or obj.type != 'EMPTY' or obj.empty_display_type != 'IMAGE':
        return

    props = obj.simple_crop
    current_data = obj.data

    # Si l'image affichée n'est pas notre "TEX_REF" et est différente de notre source stockée
    if current_data and not current_data.name.startswith("TEX_REF_"):
        if props.source_image != current_data:
            props.source_image = current_data
            reset_crop_settings(props, current_data)
            print("[Crop Tool] Synchronisation auto : Nouvelle source détectée.")

# --- LOGIQUE DE CROP ---
def crop_image_logic(context):
    obj = context.object
    props = obj.simple_crop
    orig_img = props.source_image
    
    if not orig_img: return

    # 1. Récupération du cache (instantané après le 1er clic)
    pixels_np = get_np_array(orig_img)
    src_h, src_w, _ = pixels_np.shape
    
    # 2. Calculs des dimensions % -> px
    crop_w = max(1, int(src_w * (props.crop_x / 100.0)))
    crop_h = max(1, int(src_h * (props.crop_y / 100.0)))
    
    start_x = int((src_w - crop_w) * (props.pos_x / 100.0))
    start_y = int((src_h - crop_h) * (props.pos_y / 100.0))
    
    # 3. Création/Mise à jour de l'image de sortie
    new_name = f"TEX_REF_{orig_img.name}"[:60]
    
    if new_name in bpy.data.images:
        new_img = bpy.data.images[new_name]
        if new_img.size[0] != crop_w or new_img.size[1] != crop_h:
            new_img.scale(crop_w, crop_h)
    else:
        new_img = bpy.data.images.new(new_name, width=crop_w, height=crop_h)

    # 4. Slicing NumPy (Super rapide)
    cropped_array = pixels_np[start_y : start_y + crop_h, start_x : start_x + crop_w, :]
    new_img.pixels = cropped_array.flatten()

    # 5. On assigne, mais le handler ignorera cette image car elle commence par TEX_REF_
    obj.data = new_img

# --- UI & BOILERPLATE ---
class SimpleEmptyCropProps(bpy.types.PropertyGroup):
    source_image: bpy.props.PointerProperty(type=bpy.types.Image, name="Source")
    crop_x: bpy.props.FloatProperty(name="Largeur %", default=100.0, min=1.0, max=100.0, subtype='PERCENTAGE')
    crop_y: bpy.props.FloatProperty(name="Hauteur %", default=100.0, min=1.0, max=100.0, subtype='PERCENTAGE')
    pos_x:  bpy.props.FloatProperty(name="Position X %", default=50.0, min=0.0, max=100.0, subtype='PERCENTAGE')
    pos_y:  bpy.props.FloatProperty(name="Position Y %", default=50.0, min=0.0, max=100.0, subtype='PERCENTAGE')

class OBJECT_OT_apply_crop(bpy.types.Operator):
    bl_idname = "empty.apply_crop"
    bl_label = "Calculer le Recadrage"
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
        self.layout.operator("empty.apply_crop",text="Appliquer le Crop")
        c = self.layout.column(align=True)
        p = bpy.context.object.simple_crop
        c.prop(p, "crop_x")
        c.prop(p, "crop_y")
        c.separator()
        c.prop(p, "pos_x")
        c.prop(p, "pos_y")

def register():
    bpy.utils.register_class(SimpleEmptyCropProps)
    bpy.utils.register_class(OBJECT_OT_apply_crop)
    bpy.utils.register_class(DATA_PT_empty_crop_ui)
    bpy.types.Object.simple_crop = bpy.props.PointerProperty(type=SimpleEmptyCropProps)
    # On ajoute le surveillant
    bpy.app.handlers.depsgraph_update_post.append(sync_empty_source_handler)

def unregister():
    # On retire le surveillant
    if sync_empty_source_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(sync_empty_source_handler)
    bpy.utils.unregister_class(SimpleEmptyCropProps)
    bpy.utils.unregister_class(OBJECT_OT_apply_crop)
    bpy.utils.unregister_class(DATA_PT_empty_crop_ui)
    del bpy.types.Object.simple_crop
    PIXEL_CACHE.clear()

if __name__ == "__main__":
    register()

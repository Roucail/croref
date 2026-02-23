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
        w, h = image.size
        # On charge les pixels originaux (0.0 à 1.0)
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
    props.use_transparency = False

# --- HANDLER DE SYNCHRONISATION ---
@bpy.app.handlers.persistent
def sync_empty_source_handler(scene):
    obj = bpy.context.object
    if not obj or obj.type != 'EMPTY' or obj.empty_display_type != 'IMAGE':
        return

    props = obj.simple_crop
    current_data = obj.data

    if not current_data:
        return

    if not current_data.name.startswith(PREFIX_NAME):
        if props.source_image != current_data:
            props.source_image = current_data
            reset_crop_settings(props)
            print(f"[Crop Tool] Source mise à jour : {current_data.name}")

# --- LOGIQUE DE CROP ET TRANSPARENCE ---
def crop_image_logic(context):
    obj = context.object
    props = obj.simple_crop
    orig_img = props.source_image
    
    if not orig_img: return

    # 1. Récupération des pixels originaux depuis le cache
    base_pixels = get_np_array(orig_img)
    if base_pixels is None: return
    src_h, src_w, _ = base_pixels.shape
    
    # 2. Calcul des dimensions du crop
    crop_w = max(1, int(src_w * (props.crop_x / 100.0)))
    crop_h = max(1, int(src_h * (props.crop_y / 100.0)))
    
    start_x = int((src_w - crop_w) * (props.pos_x / 100.0))
    start_y = int((src_h - crop_h) * (props.pos_y / 100.0))
    
    # 3. Slicing du rectangle de l'image (copie pour ne pas corrompre le cache)
    working_pixels = base_pixels[start_y : start_y + crop_h, start_x : start_x + crop_w, :].copy()
    
    # 4. Application de la transparence (Chroma Key)
    if props.use_transparency:
        # Couleur cible (R, G, B)
        target_rgb = np.array(props.transparency_color[:3])
        
        # Calcul de la distance L1 : Somme des valeurs absolues des différences
        # working_pixels[:,:,:3] isole RGB, on soustrait la cible, abs() puis somme sur l'axe des couleurs
        diff = np.abs(working_pixels[:, :, :3] - target_rgb)
        distance_l1 = np.sum(diff, axis=2)
        
        # Création du masque : pixels dont la distance est inférieure au seuil
        mask = distance_l1 < props.transparency_threshold
        
        # On passe l'alpha à 0 pour ces pixels
        working_pixels[mask, 3] = 0.0

    # 5. Nommage et création du bloc Image Blender
    clean_img_name = orig_img.name
    if clean_img_name.startswith(PREFIX_NAME):
        clean_img_name = clean_img_name.split("_", 2)[-1] # Nettoyage si déjà préfixé
        
    new_name = f"{PREFIX_NAME}{obj.name}_{clean_img_name}"[:63]
    
    if new_name in bpy.data.images:
        new_img = bpy.data.images[new_name]
        if new_img.size[0] != crop_w or new_img.size[1] != crop_h:
            new_img.scale(crop_w, crop_h)
    else:
        new_img = bpy.data.images.new(new_name, width=crop_w, height=crop_h)

    # 6. Mise à jour des pixels et assignation
    new_img.pixels = working_pixels.flatten()
    obj.data = new_img
    
def update_crop_callback(self, context):
    """Callback déclenché par chaque modification d'UI."""
    if self.source_image and not self.source_image.name.startswith(PREFIX_NAME):
        if self.auto_update:
            crop_image_logic(context)

# --- UI & PROPRIÉTÉS ---
class SimpleEmptyCropProps(bpy.types.PropertyGroup):
    source_image: bpy.props.PointerProperty(type=bpy.types.Image, name="Image Source")
    auto_update: bpy.props.BoolProperty(name="Auto", default=True)
    
    # Crop
    crop_x: bpy.props.FloatProperty(name="Largeur %", default=100.0, min=1.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)
    crop_y: bpy.props.FloatProperty(name="Hauteur %", default=100.0, min=1.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)
    pos_x:  bpy.props.FloatProperty(name="Position X %", default=50.0, min=0.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)
    pos_y:  bpy.props.FloatProperty(name="Position Y %", default=50.0, min=0.0, max=100.0, subtype='PERCENTAGE', update=update_crop_callback)
    
    # Transparence
    use_transparency: bpy.props.BoolProperty(
        name="Activer Transparence", 
        default=False,
        update=update_crop_callback
    )
    transparency_color: bpy.props.FloatVectorProperty(
        name="Couleur à masquer",
        subtype='COLOR', # Ceci active l'interface type matériau
        default=(0.0, 0.0, 0.0),
        size=3,
        min=0.0, max=1.0,
        update=update_crop_callback
    )
    transparency_threshold: bpy.props.FloatProperty(
        name="Seuil (L1)",
        description="Tolérance de la couleur (0 = exact)",
        default=0.1, min=0.0, max=3.0,
        update=update_crop_callback
    )

class OBJECT_OT_apply_crop(bpy.types.Operator):
    bl_idname = "empty.apply_crop"
    bl_label = "Recadrer"
    def execute(self, context):
        crop_image_logic(context)
        return {'FINISHED'}

class DATA_PT_empty_crop_ui(bpy.types.Panel):
    bl_label = "Crop & Transparence"
    bl_space_type = 'PROPERTIES'; bl_region_type = 'WINDOW'; bl_context = "data"
    
    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'EMPTY' and context.object.empty_display_type == 'IMAGE'

    def draw(self, layout):
        obj = bpy.context.object
        p = obj.simple_crop
        
        self.layout.prop(p, "source_image")
        
        row = self.layout.row(align=True)
        row.operator("empty.apply_crop", icon='IMAGE')
        row.prop(p, "auto_update", text="Auto", toggle=True)
        
        # Section Crop
        box = self.layout.box()
        box.label(text="Dimensions", icon='PIVOT_MEDIAN')
        col = box.column(align=True)
        col.prop(p, "crop_x")
        col.prop(p, "crop_y")
        col.separator()
        col.prop(p, "pos_x")
        col.prop(p, "pos_y")

        # Section Transparence
        box = self.layout.box()
        box.prop(p, "use_transparency", icon='NODE_INSERT_ON' if p.use_transparency else 'NODE_INSERT_OFF')
    
        # L'interface de sélection de couleur
        box.template_color_picker(p, "transparency_color", value_slider=True)
        box.prop(p, "transparency_color", text="")
        box.prop(p, "transparency_threshold", text="Souplesse", slider=True)

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

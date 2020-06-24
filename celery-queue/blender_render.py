import bpy
from bpy import context
import os
import time
import tempfile
from pathlib import Path
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1 :]
bvh_file_name = argv[0]

bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)

bpy.ops.import_scene.fbx(
    filepath="/queue/gesturer_mesh.fbx",
    global_scale=1,
    automatic_bone_orientation=True,
    axis_up="Y",
)

scene = context.scene


fbx_model = scene.objects["Armature"]


camera = bpy.data.objects["Camera"]
camera.location = (0, -1.54, 0.42)
camera.rotation_euler = (1.57, 0.0, 0)

lamp = bpy.data.objects["Light"]
lamp.location = (0.0, -6, 0)


if not fbx_model.animation_data:
    fbx_model.animation_data_create()
fbx_model.animation_data.action = None

mat = bpy.data.materials["Material"]


def fix_obj(parent_obj):
    for obj in parent_obj.children:
        fix_obj(obj)
    parent_obj.rotation_euler.x = 0
    if parent_obj.name in ["pCube0", "pCube1", "pCube2"]:
        parent_obj.location.y = -13
    if parent_obj.name == "pCube3":
        parent_obj.location.y = -10
    if parent_obj.name == "pCube5":
        parent_obj.location.y = -9.5

    if "materials" in dir(parent_obj.data):
        if parent_obj.data.materials:
            parent_obj.data.materials[0] = mat
        else:
            parent_obj.data.materials.append(mat)


fix_obj(fbx_model)

old_objs = set(scene.objects)
res = bpy.ops.import_anim.bvh(
    filepath=bvh_file_name,
    global_scale=0.01,
    use_fps_scale=True,
    update_scene_fps=True,
    update_scene_duration=True,
)

bvh_obj, = set(context.scene.objects) - old_objs

for pb in fbx_model.pose.bones:
    ct = pb.constraints.new("COPY_ROTATION")
    ct.owner_space = "WORLD"
    ct.target_space = "WORLD"
    ct.name = pb.name
    ct.target = bvh_obj
    ct.subtarget = pb.name


action = bvh_obj.animation_data.action
total_frames = action.frame_range.y
f = action.frame_range.x

# add a keyframe to each frame of new rig
while f < total_frames:
    scene.frame_set(f)
    for pb in fbx_model.pose.bones:
        m = fbx_model.convert_space(pose_bone=pb, matrix=pb.matrix, to_space="LOCAL")

        if pb.rotation_mode == "QUATERNION":
            pb.rotation_quaternion = m.to_quaternion()
            pb.keyframe_insert("rotation_quaternion", frame=f)
        else:
            pb.rotation_euler = m.to_euler(pb.rotation_mode)
            pb.keyframe_insert("rotation_euler", frame=f)
        # pb.location = m.to_translation()

        pb.keyframe_insert("location", frame=f)
    f += 1

print(f"total_frames {total_frames}", flush=True)


bpy.context.scene.frame_end = total_frames
tmp_dir = Path(tempfile.mkdtemp()) / "video"

bpy.context.scene.render.filepath = str(tmp_dir)

bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
# bpy.context.scene.render.image_settings.file_format = "PNG"

# Set output format
bpy.context.scene.render.ffmpeg.format = "MPEG4"

# Set the codec
bpy.context.scene.render.ffmpeg.codec = "H264"

bpy.ops.render.render(animation=True, write_still=False)
# bpy.ops.render.render(write_still=True)


print("output_file", str(list(tmp_dir.parent.glob("*"))[0]))

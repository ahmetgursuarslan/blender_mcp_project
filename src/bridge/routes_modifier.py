import bpy


def handle_manage_modifier(params: dict) -> dict:
    """Modifier CRUD: add/remove/apply/set_property/move_up/move_down/list."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"status": "error", "message": f"Object '{obj_name}' not found."}

    action = params.get("action")

    if action == "list":
        mods = []
        for m in obj.modifiers:
            mod_data = {"name": m.name, "type": m.type, "show_viewport": m.show_viewport, "show_render": m.show_render}
            for prop in ['levels', 'render_levels', 'width', 'segments', 'offset', 'count',
                         'thickness', 'angle_limit', 'iterations', 'use_mirror_x',
                         'use_mirror_y', 'use_mirror_z', 'mid_level', 'strength']:
                if hasattr(m, prop):
                    val = getattr(m, prop)
                    mod_data[prop] = list(val) if hasattr(val, '__iter__') else val
            mods.append(mod_data)
        return {"status": "success", "data": mods}

    elif action == "add":
        mtype = params.get("modifier_type", "SUBSURF")
        mname = params.get("name", mtype)
        try:
            mod = obj.modifiers.new(name=mname, type=mtype)
        except Exception as e:
            return {"status": "error", "message": f"Failed to add modifier '{mtype}': {e}"}
        props = params.get("properties", {})
        for k, v in props.items():
            try:
                if hasattr(mod, k):
                    setattr(mod, k, v)
            except Exception:
                pass
        return {"status": "success", "data": {"name": mod.name, "type": mod.type}}

    elif action == "remove":
        mod_name = params.get("name")
        mod = obj.modifiers.get(mod_name)
        if mod:
            obj.modifiers.remove(mod)
            return {"status": "success", "message": f"Modifier '{mod_name}' removed."}
        return {"status": "error", "message": f"Modifier '{mod_name}' not found."}

    elif action == "apply":
        mod_name = params.get("name")
        mod = obj.modifiers.get(mod_name)
        if mod:
            bpy.context.view_layer.objects.active = obj
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                return {"status": "success", "message": f"Modifier '{mod_name}' applied."}
            except Exception as e:
                return {"status": "error", "message": f"Apply failed: {e}"}
        return {"status": "error", "message": f"Modifier '{mod_name}' not found."}

    elif action == "set_property":
        mod_name = params.get("name")
        mod = obj.modifiers.get(mod_name)
        if not mod:
            return {"status": "error", "message": f"Modifier '{mod_name}' not found."}
        props = params.get("properties", {})
        applied = []
        for k, v in props.items():
            try:
                if hasattr(mod, k):
                    setattr(mod, k, v)
                    applied.append(k)
            except Exception as e:
                pass
        return {"status": "success", "message": f"Set properties on '{mod_name}': {applied}"}

    elif action == "move_up":
        mod_name = params.get("name")
        mod = obj.modifiers.get(mod_name)
        if mod:
            bpy.context.view_layer.objects.active = obj
            idx = list(obj.modifiers).index(mod)
            if idx > 0:
                bpy.ops.object.modifier_move_up(modifier=mod.name)
            return {"status": "success", "message": f"Modifier '{mod_name}' moved up."}
        return {"status": "error", "message": f"Modifier '{mod_name}' not found."}

    elif action == "move_down":
        mod_name = params.get("name")
        mod = obj.modifiers.get(mod_name)
        if mod:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_move_down(modifier=mod.name)
            return {"status": "success", "message": f"Modifier '{mod_name}' moved down."}
        return {"status": "error", "message": f"Modifier '{mod_name}' not found."}

    return {"status": "error", "message": f"Unknown modifier action: {action}"}


def handle_manage_constraint(params: dict) -> dict:
    """Constraint CRUD: add/remove/list."""
    obj_name = params.get("object")
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"status": "error", "message": f"Object '{obj_name}' not found."}

    action = params.get("action")

    if action == "list":
        constraints = []
        for c in obj.constraints:
            cdata = {"name": c.name, "type": c.type, "mute": c.mute, "influence": c.influence}
            if hasattr(c, 'target') and c.target:
                cdata["target"] = c.target.name
            constraints.append(cdata)
        return {"status": "success", "data": constraints}

    elif action == "add":
        ctype = params.get("constraint_type", "TRACK_TO")
        try:
            con = obj.constraints.new(type=ctype)
        except Exception as e:
            return {"status": "error", "message": f"Failed to add constraint '{ctype}': {e}"}
        if "name" in params:
            con.name = params["name"]
        props = params.get("properties", {})
        for k, v in props.items():
            try:
                if k == "target":
                    v = bpy.data.objects.get(v)
                if hasattr(con, k):
                    setattr(con, k, v)
            except Exception:
                pass
        return {"status": "success", "data": {"name": con.name, "type": con.type}}

    elif action == "remove":
        con_name = params.get("name")
        con = obj.constraints.get(con_name)
        if con:
            obj.constraints.remove(con)
            return {"status": "success", "message": f"Constraint '{con_name}' removed."}
        return {"status": "error", "message": f"Constraint '{con_name}' not found."}

    return {"status": "error", "message": f"Unknown constraint action: {action}"}

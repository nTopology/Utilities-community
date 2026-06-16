import subprocess
import os
import math
import re
import argparse

# =============================================================================
# FILE GENERATION
# =============================================================================

def create_avl_file(wing_name, mach, wing_area, mac_w, b_w, x_cg, y_cg, z_cg,
                    z_wing, c_w_root, c_w_tip, sweep_tan_w, aileron_y_start, aileron_y_end, aileron_hinge,
                    xle_h_root, z_htail, c_h_root, c_h_tip, b_h, sweep_tan_h, hstab_incidence, 
                    elevator_y_start, elevator_y_end, elevator_width,
                    xle_v_root, z_vtail, c_v_root, c_v_tip, b_v, sweep_tan_v, 
                    rudder_z_start, rudder_z_end, rudder_hinge):
    
    avl_str = f"""{wing_name}
{mach}                       ! Mach
0 0 0.0                      ! iYsym  iZsym  Zsym
{wing_area:.4f} {mac_w:.4f} {b_w:.4f}  ! Sref  Cref  Bref
{x_cg:.4f} {y_cg:.4f} {z_cg:.4f}  ! Xref  Yref  Zref
"""

    # Helper function to dynamically build surfaces without duplicate section crashes
    def build_surface(surf_name, index, x_offset, z_offset, span, c_root, c_tip, sweep_tan, 
                      ctrl_name, ctrl_start, ctrl_end, ctrl_hinge, 
                      is_vtail=False, incidence=0.0):
        
        semi = span / 2.0 if not is_vtail else span
        
        # Determine unique station coordinates (using a 1mm tolerance to avoid duplicates)
        stations = [0.0]
        if ctrl_start > 0.001:
            stations.append(ctrl_start)
        if ctrl_end > ctrl_start + 0.001 and ctrl_end < semi - 0.001:
            stations.append(ctrl_end)
        if semi > 0.001:
            stations.append(semi)
            
        # Build the headers (12 chordwise, 20 spanwise vortices)
        sections_str = f"\n# =====================================================================\n"
        sections_str += f"SURFACE\n{surf_name}\n12 1.0 20 -1.0\nINDEX\n{index}\n"
        
        # Helper to generate a single SECTION text block
        def make_sec(span_pos, side_mult):
            y_pos = span_pos * side_mult if not is_vtail else 0.0
            z_pos = z_offset + (span_pos if is_vtail else 0.0)
            x_pos = x_offset + (span_pos * sweep_tan)
            c_pos = c_root - (c_root - c_tip) * (span_pos / semi)
            
            sec = f"\nSECTION\n{x_pos:.4f}  {y_pos:.4f}  {z_pos:.4f}  {c_pos:.4f}  {incidence:.2f}\n"
            sec += "AFILE\nsd7062.txt\n" if (surf_name == "Main Wing") else "NACA\n0015\n"
            
            # If this station is within the control surface bounds, apply the CONTROL keyword
            if span_pos >= ctrl_start - 0.001 and span_pos <= ctrl_end + 0.001:
                # Ailerons invert sign on the right side; elevators and rudders do not
                sgn = 1.0
                if ctrl_name == "aileron":
                    sgn = -1.0 if side_mult > 0 else 1.0
                
                if ctrl_name == "elevator":
                    local_hinge_frac = 1.0 - (ctrl_hinge / c_pos)
                    sec += f"CONTROL\n{ctrl_name}  {sgn}  {local_hinge_frac:.4f}  0 0 0\n"
                else:
                    sec += f"CONTROL\n{ctrl_name}  {sgn}  {ctrl_hinge:.4f}  0 0 0\n"
            return sec

        # Build left side (Skipped for V-Tails)
        if not is_vtail:
            for pos in reversed(stations[1:]): 
                sections_str += make_sec(pos, -1.0)
        
        # Build right side (or full span for V-Tails)
        for pos in stations:
            sections_str += make_sec(pos, 1.0)
            
        return sections_str

    # Execute dynamic builds
    avl_str += build_surface("Main Wing", 1, 0.0, z_wing, b_w, c_w_root, c_w_tip, sweep_tan_w, 
                             "aileron", aileron_y_start, aileron_y_end, aileron_hinge)
    
    # CHANGED: Passes the absolute physical elevator width instead of a static fraction
    avl_str += build_surface("Horizontal Tail", 2, xle_h_root, z_htail, b_h, c_h_root, c_h_tip, sweep_tan_h,
                             "elevator", elevator_y_start, elevator_y_end, elevator_width, incidence=hstab_incidence)

    avl_str += build_surface("Vertical Tail", 3, xle_v_root, z_vtail, b_v, c_v_root, c_v_tip, sweep_tan_v, 
                             "rudder", rudder_z_start, rudder_z_end, rudder_hinge, is_vtail=True)

    with open(f"{wing_name}.avl", "w") as f:
        f.write(avl_str)


def create_mass_file(wing_name, mass, x_cg, y_cg, z_cg, ixx, iyy, izz):
    mass_str = f"""# {wing_name} mass profile
{mass:.6f} {x_cg:.6f} {y_cg:.6f} {z_cg:.6f}
{ixx:.6f} {iyy:.6f} {izz:.6f} 0.0 0.0 0.0
"""
    with open(f"{wing_name}.mass", "w") as f:
        f.write(mass_str)


def create_run_script(wing_name, alpha, p_nd, q_nd, r_nd):
    run_str = f"""mass
{wing_name}.mass
oper
a a {alpha}
d2 pm 0
x
st
{wing_name}.st
ft
{wing_name}_base.ft
d2 d2 0
r r {p_nd}
d1 rm 0
x
ft
{wing_name}_roll.ft
r r 0
d1 d1 0
p p {q_nd}
d2 pm 0
x
ft
{wing_name}_pitch.ft
q q 0
d2 d2 0
y y {r_nd}
d3 ym 0
x
ft
{wing_name}_yaw.ft

quit
"""
    with open("avl_commands.txt", "w") as f:
        f.write(run_str)


# =============================================================================
# EXECUTION
# =============================================================================

def run_avl(wing_name):
    with open("avl_commands.txt", "r") as cmd:
        result = subprocess.run(
            ["avl352.exe", f"{wing_name}.avl"],  
            stdin=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    if not os.path.exists(f"{wing_name}_base.ft"):
        print("\n--- AVL CRASH DETECTED ---")
        lines = result.stdout.strip().split('\n')
        for line in lines[-25:]:
            print(line)
        print("--------------------------\n")
        raise RuntimeError("AVL failed to produce output - check geometry and inputs above")
    return result.stdout


# =============================================================================
# RESULTS PARSING
# =============================================================================

def _extract(pattern, text, cast=float):
    m = re.search(pattern, text)
    return cast(m.group(1)) if m else None

def parse_results(wing_name, xref, mac):
    st_file = f"{wing_name}.st"
    base_ft = f"{wing_name}_base.ft"
    roll_ft = f"{wing_name}_roll.ft"
    pitch_ft = f"{wing_name}_pitch.ft"
    yaw_ft = f"{wing_name}_yaw.ft"

    CL = CD = Cm = elev_trim = ail_req = elev_req = rud_req = None
    Cma = Cmq = Cnb = Clb = Clp = Xnp = None

    if os.path.exists(base_ft):
        text = open(base_ft).read()
        CL  = _extract(r"CLtot\s*=\s*([-\d.]+)", text)
        CD  = _extract(r"CDtot\s*=\s*([-\d.]+)", text)
        Cm  = _extract(r"Cmtot\s*=\s*([-\d.]+)", text)
        elev_trim = _extract(r"elevator\s*=\s*([-\d.]+)", text)

    if os.path.exists(st_file):
        text = open(st_file).read()
        Cma = _extract(r"Cma\s*=\s*([-\d.]+)", text)
        Cmq = _extract(r"Cmq\s*=\s*([-\d.]+)", text)
        Cnb = _extract(r"Cnb\s*=\s*([-\d.]+)", text)
        Clb = _extract(r"Clb\s*=\s*([-\d.]+)", text)
        Clp = _extract(r"Clp\s*=\s*([-\d.]+)", text)
        Xnp = _extract(r"Xnp\s*=\s*([-\d.]+)", text)

    if os.path.exists(roll_ft):
        ail_req = _extract(r"aileron\s*=\s*([-\d.]+)", open(roll_ft).read())
    
    if os.path.exists(pitch_ft):
        elev_req = _extract(r"elevator\s*=\s*([-\d.]+)", open(pitch_ft).read())
        
    if os.path.exists(yaw_ft):
        rud_req = _extract(r"rudder\s*=\s*([-\d.]+)", open(yaw_ft).read())

    static_margin = ((Xnp - xref) / mac * 100) if (Xnp is not None and mac > 0) else 0.0

    csv_output = f"{CL},{CD},{Cm},{Cma},{Cmq},{Cnb},{Clb},{Clp},{static_margin:.2f},{elev_trim},{ail_req},{elev_req},{rud_req}"
    return csv_output


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="nTop to AVL Orchestrator for Conventional UAV")
    
    parser.add_argument("--wing_area", type=float, required=True)
    parser.add_argument("--wing_ar", type=float, required=True)
    parser.add_argument("--wing_taper", type=float, required=True)
    parser.add_argument("--wing_sweep_c4", type=float, required=True)
    parser.add_argument("--z_wing", type=float, required=True)
    
    parser.add_argument("--hstab_area", type=float, required=True)
    parser.add_argument("--hstab_ar", type=float, required=True)
    parser.add_argument("--hstab_taper", type=float, required=True)
    parser.add_argument("--z_htail", type=float, required=True)
    parser.add_argument("--hstab_incidence", type=float, required=True)
    
    parser.add_argument("--vstab_area", type=float, required=True)
    parser.add_argument("--vstab_ar", type=float, required=True)
    parser.add_argument("--vstab_taper", type=float, required=True)
    parser.add_argument("--z_vtail", type=float, required=True)
    
    parser.add_argument("--tail_moment_arm", type=float, required=True)
    parser.add_argument("--x_cg", type=float, required=True)
    parser.add_argument("--y_cg", type=float, required=True)
    parser.add_argument("--z_cg", type=float, required=True)
    
    parser.add_argument("--aileron_y_start_frac", type=float, required=True)
    parser.add_argument("--aileron_y_end_frac", type=float, required=True)
    parser.add_argument("--aileron_chord_frac", type=float, required=True)
    
    parser.add_argument("--elevator_y_start_frac", type=float, required=False, default=0.0)
    parser.add_argument("--elevator_y_end_frac", type=float, required=False, default=1.0)
    parser.add_argument("--elevator_chord_frac", type=float, required=True)
    
    parser.add_argument("--rudder_z_start_frac", type=float, required=False, default=0.0)
    parser.add_argument("--rudder_z_end_frac", type=float, required=False, default=1.0)
    parser.add_argument("--rudder_chord_frac", type=float, required=True)
    
    parser.add_argument("--mach", type=float, required=True)
    parser.add_argument("--alpha", type=float, required=True)
    
    parser.add_argument("--roll_rate", type=float, required=False, default=0.0)
    parser.add_argument("--pitch_rate", type=float, required=False, default=0.0)
    parser.add_argument("--yaw_rate", type=float, required=False, default=0.0)

    parser.add_argument("--mass", type=float, required=False, default=0.341034)
    parser.add_argument("--ixx", type=float, required=False, default=0.014441)
    parser.add_argument("--iyy", type=float, required=False, default=0.006484)
    parser.add_argument("--izz", type=float, required=False, default=0.020536)

    args = parser.parse_args()
    wing_name = "Conventional_UAV"

    # 1. DERIVED WING GEOMETRY
    b_w = math.sqrt(args.wing_area * args.wing_ar)
    semi_w = b_w / 2.0
    c_w_root = (2 * args.wing_area) / (b_w * (1 + args.wing_taper))
    c_w_tip = c_w_root * args.wing_taper
    mac_w = (2/3) * c_w_root * ((1 + args.wing_taper + args.wing_taper**2) / (1 + args.wing_taper))
    
    sweep_tan_w = math.tan(math.radians(args.wing_sweep_c4)) + (0.25 * (c_w_root - c_w_tip) / semi_w)
    
    aileron_y_start = semi_w * args.aileron_y_start_frac
    aileron_y_end = semi_w * args.aileron_y_end_frac
    aileron_hinge = 1.0 - args.aileron_chord_frac

    # 2. DERIVED H-TAIL GEOMETRY
    b_h = math.sqrt(args.hstab_area * args.hstab_ar)
    semi_h = b_h / 2.0
    c_h_root = (2 * args.hstab_area) / (b_h * (1 + args.hstab_taper))
    c_h_tip = c_h_root * args.hstab_taper
    xle_h_root = args.tail_moment_arm
    sweep_tan_h = (c_h_root - c_h_tip) / semi_h  
    
    elevator_y_start = semi_h * args.elevator_y_start_frac
    elevator_y_end = semi_h * args.elevator_y_end_frac
    
    elevator_width = args.elevator_chord_frac * ((c_h_root + c_h_tip) / 2.0)
    if elevator_width >= c_h_tip:
        raise ValueError(
            f"elevator_chord_frac={args.elevator_chord_frac} with hstab_taper={args.hstab_taper} "
            f"gives elevator_width={elevator_width:.4f} m >= c_h_tip={c_h_tip:.4f} m. "
            f"The hinge line would exit the tip chord. Reduce elevator_chord_frac below "
            f"{2 * args.hstab_taper / (1 + args.hstab_taper):.3f}."
        )

    # 3. DERIVED V-TAIL GEOMETRY
    b_v = math.sqrt(args.vstab_area * args.vstab_ar) 
    c_v_root = (2 * args.vstab_area) / (b_v * (1 + args.vstab_taper))
    c_v_tip = c_v_root * args.vstab_taper
    xle_v_root = args.tail_moment_arm
    sweep_tan_v = (c_v_root - c_v_tip) / b_v  
    
    rudder_z_start = b_v * args.rudder_z_start_frac
    rudder_z_end = b_v * args.rudder_z_end_frac
    rudder_hinge = 1.0 - args.rudder_chord_frac

    # RATE CONVERSIONS
    V_m_s = args.mach * 340.3
    p_nd = (math.radians(args.roll_rate) * b_w) / (2.0 * V_m_s)
    q_nd = (math.radians(args.pitch_rate) * mac_w) / (2.0 * V_m_s)
    r_nd = (math.radians(args.yaw_rate) * b_w) / (2.0 * V_m_s)

    create_avl_file(
        wing_name, args.mach, args.wing_area, mac_w, b_w, args.x_cg, args.y_cg, args.z_cg,
        args.z_wing, c_w_root, c_w_tip, sweep_tan_w, aileron_y_start, aileron_y_end, aileron_hinge,
        xle_h_root, args.z_htail, c_h_root, c_h_tip, b_h, sweep_tan_h, args.hstab_incidence, 
        elevator_y_start, elevator_y_end, elevator_width,
        xle_v_root, args.z_vtail, c_v_root, c_v_tip, b_v, sweep_tan_v, 
        rudder_z_start, rudder_z_end, rudder_hinge
    )
    
    create_mass_file(
        wing_name, args.mass, args.x_cg, args.y_cg, args.z_cg, args.ixx, args.iyy, args.izz
    )
    
    create_run_script(wing_name, args.alpha, p_nd, q_nd, r_nd)

    for ext in [".st", ".mass", "_base.ft", "_roll.ft", "_pitch.ft", "_yaw.ft"]:
        if os.path.exists(f"{wing_name}{ext}"):
            os.remove(f"{wing_name}{ext}")

    run_avl(wing_name)
    
    csv_output = parse_results(wing_name, args.x_cg, mac_w)
    print(csv_output)
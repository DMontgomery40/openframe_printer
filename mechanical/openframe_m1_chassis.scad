// OpenFrame M1 Rev A conceptual chassis
// Units: millimeters. This is a geometry scaffold for module envelopes.

frame_w = 390;
frame_d = 360;
frame_h = 235;
wall = 3;

module_color_alpha = 0.35;

module base_frame() {
    difference() {
        cube([frame_w, frame_d, frame_h]);
        translate([wall, wall, wall]) cube([frame_w - 2*wall, frame_d - 2*wall, frame_h - wall]);
    }
}

module roller(x, y, z, dia, len, name="roller") {
    translate([x, y, z]) rotate([90,0,0]) cylinder(h=len, r=dia/2, $fn=64);
}

module paper_path() {
    // A thin sheet following the nominal paper centerline.
    hull() {
        translate([55, 25, 42]) cube([280, 1, 1]);
        translate([70, 112, 68]) cube([260, 1, 1]);
        translate([80, 180, 92]) cube([240, 1, 1]);
        translate([86, 260, 95]) cube([228, 1, 1]);
        translate([95, 340, 116]) cube([210, 1, 1]);
    }
}

module tray_module() {
    translate([35, 10, 16]) cube([320, 92, 28]);
}

module process_cartridge() {
    translate([67, 132, 82]) cube([255, 92, 86]);
    // OPC drum centered inside cartridge envelope.
    roller(195, 180, 124, 30, 230, "opc_drum");
    roller(150, 164, 116, 16, 220, "developer");
    roller(195, 156, 154, 10, 220, "pcr");
    roller(238, 180, 94, 14, 220, "transfer");
}

module led_bar() {
    translate([70, 122, 173]) cube([250, 10, 12]);
}

module fuser_module() {
    translate([76, 238, 86]) cube([235, 62, 70]);
    roller(175, 260, 128, 24, 220, "fuser_hot");
    roller(175, 275, 104, 24, 220, "fuser_pressure");
}

module electronics_bay() {
    translate([28, 250, 20]) cube([72, 86, 56]);
}

module output_path() {
    translate([70, 315, 112]) cube([250, 32, 14]);
    roller(195, 340, 122, 16, 220, "exit");
}

color([0.8,0.8,0.8], 0.18) base_frame();
color([0.2,0.6,0.9], module_color_alpha) tray_module();
color([0.1,0.1,0.1], 0.8) paper_path();
color([0.9,0.7,0.2], module_color_alpha) process_cartridge();
color([0.8,0.1,0.1], module_color_alpha) led_bar();
color([0.9,0.3,0.1], module_color_alpha) fuser_module();
color([0.2,0.8,0.2], module_color_alpha) electronics_bay();
color([0.5,0.5,0.9], module_color_alpha) output_path();

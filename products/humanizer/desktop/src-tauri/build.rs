use std::fs::{create_dir_all, File};
use std::path::PathBuf;

fn pixels(size: u32) -> Vec<u8> {
    let mut result = vec![0_u8; (size * size * 4) as usize];
    let n = size as f32;
    for y in 0..size {
        for x in 0..size {
            let xf = x as f32 / n;
            let yf = y as f32 / n;
            let center_x = xf.clamp(0.23, 0.77);
            let center_y = yf.clamp(0.23, 0.77);
            let dx = xf - center_x;
            let dy = yf - center_y;
            // Rounded blue app tile.
            let inside = dx * dx + dy * dy <= 0.23 * 0.23;
            let left = (xf - 0.36).abs() < 0.047 && (0.25..=0.75).contains(&yf);
            let right = (xf - 0.64).abs() < 0.047 && (0.25..=0.75).contains(&yf);
            let middle = (yf - 0.5).abs() < 0.045 && (0.34..=0.66).contains(&xf);
            let i = ((y * size + x) * 4) as usize;
            let rgba = if left || right || middle {
                [241, 249, 255, 255]
            } else if inside {
                [41, 97, 213, 255]
            } else {
                [0, 0, 0, 0]
            };
            result[i..i + 4].copy_from_slice(&rgba);
        }
    }
    result
}

fn main() {
    let icons = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("icons");
    create_dir_all(&icons).expect("cannot create Tauri icon directory");

    let png_path = icons.join("icon.png");
    if !png_path.exists() {
        let file = File::create(&png_path).expect("cannot create PNG icon");
        let mut encoder = png::Encoder::new(file, 64, 64);
        encoder.set_color(png::ColorType::Rgba);
        encoder.set_depth(png::BitDepth::Eight);
        let mut writer = encoder.write_header().expect("cannot encode icon header");
        writer.write_image_data(&pixels(64)).expect("cannot write icon PNG");
    }

    let ico_path = icons.join("icon.ico");
    if !ico_path.exists() {
        let mut icon_dir = ico::IconDir::new(ico::ResourceType::Icon);
        let icon = ico::IconImage::from_rgba_data(64, 64, pixels(64));
        icon_dir.add_entry(ico::IconDirEntry::encode(&icon).expect("cannot encode ICO entry"));
        icon_dir.write(File::create(&ico_path).expect("cannot create Windows icon"))
            .expect("cannot write ICO icon");
    }

    tauri_build::build();
}

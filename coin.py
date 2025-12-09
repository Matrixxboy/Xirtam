from PIL import Image, ImageDraw
import numpy as np

def remove_white(img):
    """Convert pure white areas to transparent"""
    img = img.convert("RGBA")
    new_data = []
    for r, g, b, a in img.getdata():
        # if pixel is close to white, make it transparent
        if r > 240 and g > 240 and b > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img

# Load heads/tails images
heads = remove_white(Image.open("./public/coin/heads.png"))
tails = remove_white(Image.open("./public/coin/tails.png"))

# Standard size
size = (300, 300)
heads = heads.resize(size, Image.LANCZOS)
tails = tails.resize(size, Image.LANCZOS)

frames = []
num_frames = 50
thickness = 12

for i in range(num_frames):
    angle = (i / (num_frames - 1)) * 2 * np.pi
    scale_x = abs(np.cos(angle))
    if scale_x < 0.08:
        scale_x = 0.08

    face = heads if np.cos(angle) >= 0 else tails

    new_w = max(1, int(size[0] * scale_x))
    face_scaled = face.resize((new_w, size[1]), Image.LANCZOS)
    face_scaled = remove_white(face_scaled)  # ensure transparency

    # transparent frame background
    bg = Image.new("RGBA", size, (0, 0, 0, 0))

    # edge (thickness illusion)
    if new_w < size[0] - 2:
        edge_width = size[0] - new_w
        for t in range(thickness):
            edge = Image.new("RGBA", (edge_width, size[1]), (0, 0, 0, 0))
            draw = ImageDraw.Draw(edge)
            for y in range(size[1]):
                shade = int(120 + 100 * np.sin((y / size[1]) * np.pi))
                draw.line([(0, y), (edge_width, y)], fill=(shade, shade, shade, 255))
            offset_x = (size[0] - edge_width) // 2 + t
            bg.paste(edge, (offset_x, 0), edge)

    # paste face centered (transparent)
    bg.paste(face_scaled, ((size[0] - new_w) // 2, 0), face_scaled)
    frames.append(bg)

# save animated GIF with alpha transparency
frames[0].save(
    "coin_flip_thick.gif",
    save_all=True,
    append_images=frames[1:],
    duration=45,
    loop=0,
    disposal=2,
    transparency=0
)

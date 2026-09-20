import cv2
import numpy as np
import math
import random
import tkinter as tk

def run_photomosaic_experience(image_path, grid_cols=80, grid_rows=80):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load '{image_path}'. Please ensure your image is in the same folder.")
        return

    img = cv2.convertScaleAbs(img, alpha=1.15, beta=30)

    root = tk.Tk()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.destroy()

    max_dim = min(900, screen_h - 150, screen_w - 150)
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape[:2]

    tile_w = w // grid_cols
    tile_h = h // grid_rows
    base_tile = cv2.resize(img, (tile_w, tile_h))
    
    static_tiles = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            x = c * tile_w
            y = r * tile_h
            patch = img[y:y+tile_h, x:x+tile_w]
            avg_color = np.mean(patch, axis=(0, 1))
            color_block = np.full_like(base_tile, avg_color)
            tinted = cv2.addWeighted(base_tile, 0.3, color_block, 0.7, 0)
            static_tiles.append((x, y, tinted))

    x_off = max(0, (screen_w - w) // 2)
    y_off = max(0, (screen_h - h) // 2)
    black_screen = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)

    window_name = "Photomosaic Loop (Cinematic)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def show_centered(frame_to_show):
        canvas = black_screen.copy()
        canvas[y_off:y_off+h, x_off:x_off+w] = frame_to_show
        cv2.imshow(window_name, canvas)

    while True:
        active_tiles = []
        max_delay = 15 
        for x, y, tinted in static_tiles:
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(max(w, h) * 0.6, max(w, h) * 1.1) 
            start_x = int((w / 2) + math.cos(angle) * dist)
            start_y = int((h / 2) + math.sin(angle) * dist)
            delay = random.randint(0, max_delay) 
            active_tiles.append([x, y, start_x, start_y, delay, tinted])

        mosaic = np.zeros((h, w, 3), dtype=np.uint8)
        escape_pressed = False
        swarm_frames = 75 
        
        for f in range(swarm_frames + 1):
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            for t_data in active_tiles:
                tx, ty, sx, sy, delay, tile = t_data
                if f < delay:
                    continue 
                progress = (f - delay) / (swarm_frames - delay)
                if progress > 1.0: progress = 1.0
                ease = 1 - pow(1 - progress, 4)
                curr_x = int(sx + (tx - sx) * ease)
                curr_y = int(sy + (ty - sy) * ease)
                
                if curr_x < w and curr_x + tile_w > 0 and curr_y < h and curr_y + tile_h > 0:
                    y_start = max(0, curr_y)
                    y_end = min(h, curr_y + tile_h)
                    x_start = max(0, curr_x)
                    x_end = min(w, curr_x + tile_w)
                    tile_y_start = y_start - curr_y
                    tile_y_end = tile_y_start + (y_end - y_start)
                    tile_x_start = x_start - curr_x
                    tile_x_end = tile_x_start + (x_end - x_start)
                    frame[y_start:y_end, x_start:x_end] = tile[tile_y_start:tile_y_end, tile_x_start:tile_x_end]

            show_centered(frame)
            if cv2.waitKey(16) & 0xFF == 27:
                escape_pressed = True
                break
                
        if escape_pressed: break
        
        mosaic = frame.copy()
        show_centered(mosaic)
        cv2.waitKey(1000) 

        target_c, target_r = grid_cols // 2, grid_rows // 2
        target_x1 = target_c * tile_w
        target_y1 = target_r * tile_h
        target_x2, target_y2 = target_x1 + tile_w, target_y1 + tile_h

        center_patch = img[target_y1:target_y2, target_x1:target_x2]
        center_avg_color = np.mean(center_patch, axis=(0, 1))
        tx_center, ty_center = target_x1 + tile_w / 2.0, target_y1 + tile_h / 2.0
        zoom_frames = 120 
        
        for f in range(zoom_frames + 1):
            t = f / zoom_frames
            ease = (1 - math.cos(t * math.pi)) / 2 
            view_w = w + (tile_w - w) * ease
            view_h = h + (tile_h - h) * ease
            view_cx = (w / 2.0) + (tx_center - (w / 2.0)) * ease
            view_cy = (h / 2.0) + (ty_center - (h / 2.0)) * ease
            scale_x, scale_y = w / view_w, h / view_h
            tx, ty = (w / 2.0) - view_cx * scale_x, (h / 2.0) - view_cy * scale_y
            M = np.array([[scale_x, 0, tx], [0, scale_y, ty]], dtype=np.float32)
            frame = cv2.warpAffine(mosaic, M, (w, h), flags=cv2.INTER_LINEAR)
            
            screen_x1, screen_y1 = target_x1 * scale_x + tx, target_y1 * scale_y + ty
            screen_x2, screen_y2 = target_x2 * scale_x + tx, target_y2 * scale_y + ty
            sx, sy = int(round(screen_x1)), int(round(screen_y1))
            ex, ey = int(round(screen_x2)), int(round(screen_y2))
            sw, sh = ex - sx, ey - sy

            if sw > 0 and sh > 0:
                high_res_tile = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_LINEAR)
                current_tint = 0.7 * (1.0 - ease)
                color_block = np.full_like(high_res_tile, center_avg_color)
                blended_tile = cv2.addWeighted(high_res_tile, 1.0 - current_tint, color_block, current_tint, 0)
                y_start, y_end = max(0, sy), min(h, ey)
                x_start, x_end = max(0, sx), min(w, ex)
                tile_y_start, tile_y_end = y_start - sy, sh - (ey - y_end)
                tile_x_start, tile_x_end = x_start - sx, sw - (ex - x_end)
                if y_end > y_start and x_end > x_start:
                    frame[y_start:y_end, x_start:x_end] = blended_tile[tile_y_start:tile_y_end, tile_x_start:tile_x_end]

            show_centered(frame)
            if cv2.waitKey(16) & 0xFF == 27: 
                escape_pressed = True
                break

        if escape_pressed: break

        show_centered(img)
        if cv2.waitKey(2500) & 0xFF == 27:
            break

        for f in range(zoom_frames, -1, -1):
            t = f / zoom_frames
            ease = (1 - math.cos(t * math.pi)) / 2 
            view_w = w + (tile_w - w) * ease
            view_h = h + (tile_h - h) * ease
            view_cx = (w / 2.0) + (tx_center - (w / 2.0)) * ease
            view_cy = (h / 2.0) + (ty_center - (h / 2.0)) * ease
            scale_x, scale_y = w / view_w, h / view_h
            tx, ty = (w / 2.0) - view_cx * scale_x, (h / 2.0) - view_cy * scale_y
            M = np.array([[scale_x, 0, tx], [0, scale_y, ty]], dtype=np.float32)
            frame = cv2.warpAffine(mosaic, M, (w, h), flags=cv2.INTER_LINEAR)
            
            screen_x1, screen_y1 = target_x1 * scale_x + tx, target_y1 * scale_y + ty
            screen_x2, screen_y2 = target_x2 * scale_x + tx, target_y2 * scale_y + ty
            sx, sy = int(round(screen_x1)), int(round(screen_y1))
            ex, ey = int(round(screen_x2)), int(round(screen_y2))
            sw, sh = ex - sx, ey - sy

            if sw > 0 and sh > 0:
                high_res_tile = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_LINEAR)
                current_tint = 0.7 * (1.0 - ease)
                color_block = np.full_like(high_res_tile, center_avg_color)
                blended_tile = cv2.addWeighted(high_res_tile, 1.0 - current_tint, color_block, current_tint, 0)
                y_start, y_end = max(0, sy), min(h, ey)
                x_start, x_end = max(0, sx), min(w, ex)
                tile_y_start, tile_y_end = y_start - sy, sh - (ey - y_end)
                tile_x_start, tile_x_end = x_start - sx, sw - (ex - x_end)
                if y_end > y_start and x_end > x_start:
                    frame[y_start:y_end, x_start:x_end] = blended_tile[tile_y_start:tile_y_end, tile_x_start:tile_x_end]

            show_centered(frame)
            if cv2.waitKey(16) & 0xFF == 27: 
                escape_pressed = True
                break
                
        if escape_pressed: break
        
        show_centered(mosaic)
        cv2.waitKey(1200) 

        for f in range(swarm_frames + 1):
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            for t_data in active_tiles:
                tx, ty, sx, sy, delay, tile = t_data
                reverse_delay = max_delay - delay 
                if f < reverse_delay:
                    curr_x, curr_y = tx, ty
                else:
                    progress = (f - reverse_delay) / (swarm_frames - reverse_delay)
                    if progress > 1.0: progress = 1.0
                    ease = pow(progress, 3) 
                    curr_x = int(tx + (sx - tx) * ease)
                    curr_y = int(ty + (sy - ty) * ease)
                
                if curr_x < w and curr_x + tile_w > 0 and curr_y < h and curr_y + tile_h > 0:
                    y_start = max(0, curr_y)
                    y_end = min(h, curr_y + tile_h)
                    x_start = max(0, curr_x)
                    x_end = min(w, curr_x + tile_w)
                    tile_y_start = y_start - curr_y
                    tile_y_end = tile_y_start + (y_end - y_start)
                    tile_x_start = x_start - curr_x
                    tile_x_end = tile_x_start + (x_end - x_start)
                    frame[y_start:y_end, x_start:x_end] = tile[tile_y_start:tile_y_end, tile_x_start:tile_x_end]

            show_centered(frame)
            if cv2.waitKey(16) & 0xFF == 27:
                escape_pressed = True
                break
                
        if escape_pressed: break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_photomosaic_experience('image.png', grid_cols=70, grid_rows=70)

import os
import threading
import flet as ft
from ffmpeg_normalize import FFmpegNormalize

def main(page: ft.Page):
    # --- Page Configurations ---
    page.title = "Setlist Audio Normalizer/Leveler"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 10
    page.window.width = 480
    page.window.height = 550
    page.window_resizable = True
    page.window.maximizable = False
    page.update()

    page.theme_mode = ft.ThemeMode.DARK
    

    # --- State Variables ---
    selected_path = None 
    is_folder_selected = False
    files_to_process_count = 0 
    stop_event = threading.Event()

    # --- Initialize FilePicker Service ---
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    # --- UI Component Logic ---
    def handle_selection(path, is_dir):
        nonlocal selected_path, is_folder_selected, files_to_process_count
        selected_path = path
        is_folder_selected = is_dir
        files_to_process_count = 0

        if selected_path:
            if is_folder_selected:
                audio_extensions = ('.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg') 
                for root, _, files in os.walk(selected_path):
                    if "normalized_output" in root:
                        continue
                    for file in files:
                        if file.lower().endswith(audio_extensions):
                            files_to_process_count += 1
                file_name_text.value = f"Selected Folder: {os.path.basename(selected_path)} ({files_to_process_count} audio files found)"
                file_name_text.color = ft.Colors.GREEN_400
                process_button.disabled = (files_to_process_count == 0)
            else: 
                file_name_text.value = f"Selected File: {os.path.basename(selected_path)}"
                file_name_text.color = ft.Colors.GREEN_400
                process_button.disabled = False
                files_to_process_count = 1 
        else:
            file_name_text.value = "No file or folder selected."
            file_name_text.color = ft.Colors.RED_400
            process_button.disabled = True
        page.update()

    # 🌟 FIXED: Direct modern async task returning value to your handler
    def pick_file_clicked(e):
        async def select_file_task():
            selected_files = await file_picker.pick_files(allow_multiple=False)
            if selected_files and len(selected_files) > 0:
                handle_selection(selected_files[0].path, False)
            else:
                handle_selection(None, False)
        page.run_task(select_file_task)

    def pick_folder_clicked(e):
        async def select_dir_task():
            res_path = await file_picker.get_directory_path()
            if res_path:
                handle_selection(res_path, True)
            else:
                handle_selection(None, False)
        page.run_task(select_dir_task)

    def run_normalization():
        norm_type = norm_dropdown.value
        target_level = float(target_input.value)
        output_codec = codec_dropdown.value

        files_to_add = []
        output_root_dir = ""

        if is_folder_selected:
            output_root_dir = os.path.join(selected_path, "normalized_output")
            os.makedirs(output_root_dir, exist_ok=True)
            audio_extensions = ('.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg')
            for root, _, files in os.walk(selected_path):
                if "normalized_output" in root:
                    continue
                for file in files:
                    if file.lower().endswith(audio_extensions):
                        input_file_path = os.path.join(root, file)
                        
                        relative_path = os.path.relpath(input_file_path, selected_path)
                        output_sub_dir = os.path.join(output_root_dir, os.path.dirname(relative_path))
                        os.makedirs(output_sub_dir, exist_ok=True)
                        
                        base_name, ext = os.path.splitext(file)
                        output_file_path = os.path.join(output_sub_dir, f"{base_name}_normalized{ext}")
                        files_to_add.append((input_file_path, output_file_path))
        else: 
            dir_name, file_name = os.path.split(selected_path)
            base_name, ext = os.path.splitext(file_name)
          
            output_root_dir = dir_name 
            output_file_path = os.path.join(output_root_dir, f"{base_name}_normalized{ext}")
            files_to_add.append((selected_path, output_file_path))
            
        if not files_to_add:
            status_text.value = "No audio files found to process."
            status_text.color = ft.Colors.ORANGE_400
            page.update()
            return

        try:
            processed_successfully = 0
            
            for i, (input_file_path, output_file_path) in enumerate(files_to_add):
                if stop_event.is_set():
                    break
                if ext==output_codec:
                        status_text.value = f"Processing ({i+1}/{len(files_to_add)}):\n{os.path.basename(input_file_path)}"
                        page.update()
                        page.run_thread(run_normalization)
                else:        
                    print("wrong extention")
                    #stop_event.set()
                    
                
                normalizer = FFmpegNormalize(
                    normalization_type=norm_type,
                    target_level=target_level,
                    audio_codec=output_codec,
                    video_disable=True,
                    subtitle_disable=True
                )
                
                normalizer.add_media_file(input_file_path, output_file_path)
                normalizer.run_normalization()
                processed_successfully += 1

        

            if stop_event.is_set():
                status_text.value = f"Process stopped by user. ({processed_successfully} files completed)"
                status_text.color = ft.Colors.ORANGE_400
            else:
                status_text.value = f"Success! All {len(files_to_add)} files normalized.\nSaved to: {os.path.basename(output_root_dir)}"
                status_text.color = ft.Colors.GREEN_400
            
        except Exception as ex:
            status_text.value = f"Error during processing: input and output must have same file extention."
            status_text.color = ft.Colors.YELLOW_400
           
            
        finally:
            progress_bar.visible = False
            process_button.disabled = False
            pick_file_button.disabled = False
            pick_folder_button.disabled = False
            stop_button.visible = False
            page.update()

    def trigger_stop(e):
        stop_event.set()
        stop_button.disabled = True
        status_text.value = "Stopping... finishing current file task."
        page.update()

    def start_processing(e):
        stop_event.clear()
        process_button.disabled = True
        pick_file_button.disabled = True
        pick_folder_button.disabled = True
        stop_button.visible = True
        stop_button.disabled = False
        progress_bar.visible = True
        status_text.value = "Preparing media loop... Please wait."
        status_text.color = ft.Colors.BLUE_200
        page.update()

        page.run_thread(run_normalization)

    # --- UI Layout Elements ---
    header = ft.Text(
        "Setlist Audio Normalizer", 
        theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, 
        weight=ft.FontWeight.BOLD
    )
    
    pick_file_button = ft.Button(
        "Select Media File", 
        icon=ft.Icons.AUDIO_FILE, 
        on_click=pick_file_clicked,
    )
    
    pick_folder_button = ft.Button(
        "Select Folder",
        icon=ft.Icons.FOLDER,
        on_click=pick_folder_clicked,
    )
    
    file_name_text = ft.Text("No file or folder selected.", italic=True, color=ft.Colors.GREY_500)

    norm_dropdown = ft.Dropdown(
        label="Normalization Type",
        value="ebu", 
        border_color="white",
        border_width=1,
        border_radius=5, 
        width=380,
        options=[
            ft.dropdown.Option("ebu", "EBU R128 (Loudness)"),
            ft.dropdown.Option("rms", "RMS (Root Mean Square)"),
            ft.dropdown.Option("peak", "Peak (Max Volume Limit)")
        ]
    )

    target_input = ft.TextField( 
        label="Target Level (dB / LUFS)", 
        value="-18.5", 
        width=380,
        border_color="white",
        border_width=1,
        border_radius=5,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    codec_dropdown = ft.Dropdown( 
        label="Output Audio Codec",
        value="mp3",
        width=380,
        border_color="white",
        border_width=1,
        border_radius=5,
        options=[
            ft.dropdown.Option("aac", "AAC (Standard Compressed)"),
            ft.dropdown.Option("mp3", "MP3"),
            ft.dropdown.Option("pcm_s16le", "PCM 16-bit (Uncompressed WAV)")
        ]
    )

    process_button = ft.Button( 
        "Normalize Audio", 
        icon=ft.Icons.PLAY_ARROW, 
        bgcolor=ft.Colors.BLUE_700,
        color=ft.Colors.WHITE,
        disabled=True, 
        on_click=start_processing
    )

    stop_button = ft.Button(
        "Stop Process", 
        icon=ft.Icons.STOP, 
        bgcolor=ft.Colors.RED_700,
        color=ft.Colors.WHITE,
        visible=False,
        on_click=trigger_stop
    )

    progress_bar = ft.ProgressBar(width=380, visible=False, color=ft.Colors.BLUE_400) 
    status_text = ft.Text("", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.NORMAL) 
    

    # --- App Mounting ---
    page.add(
        header,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        ft.Row(
            [pick_file_button, pick_folder_button],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        file_name_text,
        ft.Divider(height=10, color=ft.Colors.GREY_800),
        norm_dropdown,
        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
        target_input,
        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
        codec_dropdown,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        process_button,
        stop_button,
        ft.Container(content=progress_bar),
        status_text,
        
    )
    page.update()

if __name__ == "__main__":
    ft.run(main,view=ft.AppView.FLET_APP)

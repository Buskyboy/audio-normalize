
import os
import threading
import flet as ft
from ffmpeg_normalize import FFmpegNormalize

# 1. Main function remains async for the file picker
def main(page: ft.Page):
    # --- Page Configurations ---
    page.title = "Setlist Audio Normalizer/Leveler"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 10
    page.window.width =500
    page.window.height = 500
    page.theme_mode = ft.ThemeMode.DARK

    # --- State Variables ---
    selected_file_path = None

    # --- Initialize FilePicker at startup ---
    file_picker = ft.FilePicker()
    

    # --- UI Component Logic ---
    def handle_file_selection(files):
        nonlocal selected_file_path
        if files:
            selected_file_path = files[0].path
            file_name_text.value = f"Selected: {os.path.basename(selected_file_path)}"
            file_name_text.color = ft.Colors.GREEN_400
            process_button.disabled = False
        else:
            file_name_text.value = "No file selected."
            file_name_text.color = ft.Colors.RED_400
            process_button.disabled = True
        page.update()

    async def pick_file_clicked(e):
        # This one MUST keep 'await' because it opens an external OS dialog coroutine
        result = await file_picker.pick_files(allow_multiple=True)
        handle_file_selection(result)

    def run_normalization():
        norm_type = norm_dropdown.value
        target_level = float(target_input.value)
        output_codec = codec_dropdown.value

        dir_name, file_name = os.path.split(selected_file_path)
        base_name, ext = os.path.splitext(file_name)
        output_file_path = os.path.join(dir_name, f"{base_name}_normalized{ext}")

        try:
            normalizer = FFmpegNormalize(
                normalization_type=norm_type,
                target_level=target_level,
                audio_codec=output_codec,
               
            )
            
            normalizer.add_media_file(selected_file_path, output_file_path)
            normalizer.run_normalization()
           
            
            status_text.value = f"Success! Output saved to:\n{output_file_path}"
            status_text.color = ft.Colors.GREEN_400
           



            
        except Exception as ex:
            status_text.value = f"Error during processing:\n{str(ex)}"
            status_text.color = ft.Colors.RED_400
            import traceback
            traceback.print_exc() 
            
        finally:
            progress_bar.visible = False
            process_button.disabled = False
            pick_button.disabled = False
            page.update()

    def start_processing(e):
        process_button.disabled = True
        pick_button.disabled = True
        progress_bar.visible = True
        status_text.value = "Processing media... Please wait."
        status_text.color = ft.Colors.BLUE_200
        page.update()


        #my_thread= threading.Thread(target=run_normalization, daemon=True).start()
        page.run_thread(run_normalization)

       

    # --- UI Layout Elements ---
    header = ft.Text(
        "Setlist Audio Normalizer", 
        theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, 
        weight=ft.FontWeight.BOLD
    )
    
    pick_button = ft.Button(
        "Select Media File", 
        icon=ft.Icons.FOLDER_OPEN, 
        on_click=pick_file_clicked,
       
    )
    
    file_name_text = ft.Text("No file selected.", italic=True, color=ft.Colors.GREY_500)

    norm_dropdown = ft.Dropdown(
        label="Normalization Type",
        value="ebu", border_color="white",
        border_width=1,
        border_radius=5,
        width=400,
     
  
        options=[
            ft.dropdown.Option("ebu", "EBU R128 (Loudness)"),
            ft.dropdown.Option("rms", "RMS (Root Mean Square)"),
            ft.dropdown.Option("peak", "Peak (Max Volume Limit)")
        ]
    )

    target_input = ft.TextField(
        label="Target Level (dB / LUFS)", 
        value="-18.5", 
      
        width=400,
        border_color="white",
        border_width=1,
        border_radius=5,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    codec_dropdown = ft.Dropdown(
        label="Output Audio Codec",
        value="mp3",
   
        width=400,
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

    progress_bar = ft.ProgressBar(width=400, visible=False, color=ft.Colors.BLUE_400)
    status_text = ft.Text("", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.NORMAL)

    # --- App Mounting ---
  
    page.add(
        header,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        pick_button,
        file_name_text,
        ft.Divider(height=10, color=ft.Colors.GREY_800),
        norm_dropdown,
        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
        target_input,
        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),

        codec_dropdown,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        process_button,
        ft.Container(content=progress_bar),
        status_text
    )

if __name__ == "__main__":
   
   ft.app(target=main)
   #ft.run(main, view=ft.AppView.FLET_APP)

  
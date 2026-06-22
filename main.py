import os
import threading
import wx
from ffmpeg_normalize import FFmpegNormalize

class NormalizerFrame(wx.Frame): 
    def __init__(self):
        super().__init__(parent=None, title="Setlist Audio Normalizer/Leveler", size=(450, 425))

        self.CreateStatusBar().SetStatusText("Ready") # Simple 1-field bar
 
        # --- State Variables ---
        self.selected_path = None 
        self.is_folder_selected = False
        self.files_to_process_count = 0 
        self.stop_event = threading.Event()
        self.audio_extensions = ('.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg')

        self.InitUI()
        self.Centre()

    def InitUI(self):
        # Configure Dark Mode Theme Colors
        self.SetBackgroundColour(wx.Colour(20, 20, 20))
        text_color = wx.Colour(240, 240, 240)
        input_bg = wx.Colour(40, 40, 40)

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header Title
        header = wx.StaticText(panel, label="Setlist Audio Normalizer")
        header.SetForegroundColour(wx.Colour(144, 202, 249))
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        header.SetFont(font)
        main_sizer.Add(header, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 15)

        # File and Folder Picker Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.pick_file_btn = wx.Button(panel, label="Select Media File")
        self.pick_folder_btn = wx.Button(panel, label="Select Folder")
        btn_sizer.Add(self.pick_file_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.pick_folder_btn, 0, wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)

        self.pick_file_btn.Bind(wx.EVT_BUTTON, self.OnPickFile)
        self.pick_folder_btn.Bind(wx.EVT_BUTTON, self.OnPickFolder)

        # --- THE CENTERING FIX ---
        # Add style=wx.ALIGN_CENTER to the widget, and wx.EXPAND to the sizer
        self.file_name_text = wx.StaticText(panel, label="No file or folder selected.", style=wx.ALIGN_CENTER)
        self.file_name_text.SetForegroundColour(wx.Colour(150, 150, 150))
        italic_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.file_name_text.SetFont(italic_font)
        main_sizer.Add(self.file_name_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Divider
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 10)

        # Form Elements Sizer 
        form_sizer = wx.BoxSizer(wx.VERTICAL)

        # Normalization Type Dropdown
        norm_label = wx.StaticText(panel, label="Normalization Type")
        norm_label.SetForegroundColour(text_color)
        norm_choices = ["EBU R128 (Loudness)", "RMS (Root Mean Square)", "Peak (Max Volume Limit)"]
        self.norm_keys = ["ebu", "rms", "peak"]
        self.norm_dropdown = wx.Choice(panel, choices=norm_choices)
        self.norm_dropdown.SetSelection(0)
        
        # Target Level Input
        target_label = wx.StaticText(panel, label="Target Level (dB / LUFS)")
        target_label.SetForegroundColour(text_color)
        self.target_input = wx.TextCtrl(panel, value="-18.5")
        self.target_input.SetBackgroundColour(input_bg)
        self.target_input.SetForegroundColour(text_color)

        # Output Audio Codec Dropdown
        codec_label = wx.StaticText(panel, label="Output Audio Codec")
        codec_label.SetForegroundColour(text_color)
        codec_choices = ["MP3", "AAC (Standard Compressed)", "PCM 16-bit (Uncompressed WAV)"]
        self.codec_keys = ["mp3", "aac", "pcm_s16le"]
        self.codec_dropdown = wx.Choice(panel, choices=codec_choices)
        self.codec_dropdown.SetSelection(0)

        # Add form pieces to form sizer
        for label, control in [(norm_label, self.norm_dropdown), (target_label, self.target_input), (codec_label, self.codec_dropdown)]:
            form_sizer.Add(label, 0, wx.LEFT | wx.TOP, 5)
            form_sizer.Add(control, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(form_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 40)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 10)

        # Control Buttons (Normalize / Stop)
        control_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.process_button = wx.Button(panel, label="Normalize Audio")
        self.process_button.SetForegroundColour(wx.WHITE)
        self.process_button.Bind(wx.EVT_BUTTON, self.OnStartProcessing)
        control_buttons_sizer.Add(self.process_button, 0, wx.RIGHT, 10)

        self.stop_button = wx.Button(panel, label="Stop Process")
        self.stop_button.SetForegroundColour(wx.WHITE)
        self.stop_button.Bind(wx.EVT_BUTTON, self.OnTriggerStop)
        control_buttons_sizer.Add(self.stop_button, 0, 0)
        
        main_sizer.Add(control_buttons_sizer, 0, wx.ALIGN_CENTER | wx.TOP, 5)

        # Progress Indicator 
        self.progress_bar = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL)
        main_sizer.Add(self.progress_bar, 0, wx.EXPAND | wx.ALL, 20)

        # Global Application Status Text
        self.status_text = wx.StaticText(panel, label="", style=wx.ALIGN_CENTER)
        self.status_text.SetForegroundColour(wx.Colour(144, 202, 249))
        main_sizer.Add(self.status_text, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        self.Layout()

    # --- UI Event Responders ---
    def OnPickFile(self, event):
        wildcard = "Audio files (*.mp3;*.wav;*.flac;*.aac;*.m4a;*.ogg)|*.mp3;*.wav;*.flac;*.aac;*.m4a;*.ogg"
        with wx.FileDialog(self, "Select Media File", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.selected_path = fileDialog.GetPath()
            
        self.is_folder_selected = False
        self.files_to_process_count = 1
        
        self.file_name_text.SetLabel(f"Selected File: {os.path.basename(self.selected_path)}")
        self.file_name_text.SetForegroundColour(wx.Colour(102, 187, 106)) # Green 400
        self.process_button.Enable()
        self.Layout()
        self.SendSizeEvent()
        self.SetSize(451, 426)
        self.SetSize(450, 425)
           
    def OnPickFolder(self, event):
        with wx.DirDialog(self, "Select Folder", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.selected_path = dirDialog.GetPath()

        self.is_folder_selected = True
        self.files_to_process_count = 0
        
        for root, _, files in os.walk(self.selected_path):
            if "normalized_output" in root:
                continue
            for file in files:
                if file.lower().endswith(self.audio_extensions):
                    self.files_to_process_count += 1

        self.file_name_text.SetLabel(f"Selected Folder: {os.path.basename(self.selected_path)} ({self.files_to_process_count} files found)")
        self.file_name_text.SetForegroundColour(wx.Colour(102, 187, 106)) # Green 400
       
        self.process_button.Enable(self.files_to_process_count > 0)
        self.Layout()
        self.SendSizeEvent()
        self.SetSize(451, 426)
        self.SetSize(450, 425)
       
    def OnStartProcessing(self, event):
        
        self.stop_event.clear()
        self.process_button.Disable()
        self.pick_file_btn.Disable()
        self.pick_folder_btn.Disable()
        
        self.stop_button.Enable(True)
        self.progress_bar.Pulse() 
        
        self.status_text.SetLabel("Starting normalizer loop...")
        self.SetStatusText("Starting normalizer loop...")
        self.status_text.SetForegroundColour(wx.Colour(144, 202, 249)) 
        self.Layout()
        self.SendSizeEvent()
        self.SetSize(451, 426)
        self.SetSize(450, 425)
        
        # Dispatch processing to a separate thread to keep UI alive
        threading.Thread(target=self.RunNormalization, daemon=True).start()

    def OnTriggerStop(self, event):
        self.stop_event.set()
        self.stop_button.Disable()
        self.status_text.SetLabel("Stopping... finishing current audio file.")
        self.SetStatusText("Stopping... finishing current audio file. ")

    # --- Processing Thread Block ---
    def RunNormalization(self):
        # Gather Settings
        norm_type = self.norm_keys[self.norm_dropdown.GetSelection()]
        output_codec = self.codec_keys[self.codec_dropdown.GetSelection()]
        
        try:
            target_level = float(self.target_input.GetValue())
        except ValueError:
            wx.CallAfter(self.UpdateUIOnFailure, "Error: Target Level must be a number.", wx.Colour(239, 154, 154))
            return

        # Gather Files
        files_to_add = []
        if self.is_folder_selected:
            output_root_dir = os.path.join(self.selected_path, "normalized_output")
            os.makedirs(output_root_dir, exist_ok=True)
            for root, _, files in os.walk(self.selected_path):
                if "normalized_output" in root:
                    continue
                for file in files:
                    if file.lower().endswith(self.audio_extensions):
                        input_file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(input_file_path, self.selected_path)
                        output_sub_dir = os.path.join(output_root_dir, os.path.dirname(relative_path))
                        os.makedirs(output_sub_dir, exist_ok=True)
                        base_name, ext = os.path.splitext(file)
                        output_file_path = os.path.join(output_sub_dir, f"{base_name}_normalized{ext}")
                        files_to_add.append((input_file_path, output_file_path))
        else: 
            dir_name, file_name = os.path.split(self.selected_path)
            base_name, ext = os.path.splitext(file_name)
            output_file_path = os.path.join(dir_name, f"{base_name}_normalized{ext}")
            files_to_add.append((self.selected_path, output_file_path))
            
        if not files_to_add:
            wx.CallAfter(self.UpdateUIOnFailure, "No audio files found to process.", wx.Colour(255, 183, 77))
            return

        # Process Files
        try:
            processed_successfully = 0
            for i, (input_file_path, output_file_path) in enumerate(files_to_add):
                if self.stop_event.is_set():
                    break
                
                msg = f"Processing ({i+1}/{len(files_to_add)}): {os.path.basename(input_file_path)}"
                wx.CallAfter(self.SetStatusText, msg)
                
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

            if self.stop_event.is_set():
                wx.CallAfter(self.UpdateUIOnFinalStatus, f"Process stopped. ({processed_successfully} files completed)", wx.Colour(255, 183, 77))
            else:
                wx.CallAfter(self.UpdateUIOnFinalStatus, "Success! Normalized files saved.", wx.Colour(102, 187, 106))
               
        except Exception as ex:
            # Safely call MessageBox from background thread
            wx.CallAfter(wx.MessageBox, "The file extension for output must match the file being processed.", "MisMatch", wx.OK)
            wx.CallAfter(self.UpdateUIOnFailure, f"Processing Error: {str(ex)}", wx.Colour(255, 238, 88))

    # --- Thread Safe UI Mutation Methods ---
    def UpdateUIOnFailure(self, message, color):
        self.status_text.SetLabel(message)
        self.SetStatusText(message)
        self.status_text.SetForegroundColour(color)
        
        self.progress_bar.SetValue(0) # Reset gauge instead of hiding
        self.process_button.Enable(True)
        self.pick_file_btn.Enable(True)
        self.pick_folder_btn.Enable(True)
        self.Layout()
        self.SendSizeEvent()
        self.SetSize(451, 426)
        self.SetSize(450, 425)

    def UpdateUIOnFinalStatus(self, message, color):
        self.status_text.SetLabel(message)
        self.SetStatusText(message)
        self.status_text.SetForegroundColour(color)
        
        self.progress_bar.SetValue(0) # Reset gauge instead of hiding
        self.process_button.Enable(False)
        self.pick_file_btn.Enable(True)
        self.pick_folder_btn.Enable(True)
        self.Layout()
        self.SendSizeEvent()
        self.SetSize(451, 426)
        self.SetSize(450, 425)

if __name__ == "__main__":
    app = wx.App()
    frame = NormalizerFrame()
    frame.Show()
    app.MainLoop()
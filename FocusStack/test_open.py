#!/usr/bin/env python3

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp, GObject, Gio, GLib
import os
import sys

# Supported image file extensions
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
    '.webp', '.psd', '.xcf', '.svg', '.pdf', '.eps', '.raw',
    '.cr2', '.nef', '.arw', '.dng', '.exr', '.hdr'
}

class BatchFileOpener(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        return ['batch-file-opener']

    def do_create_procedure(self, name):
        if name == 'batch-file-opener':
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN,
                                              self.run, None)
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.ALWAYS)
            
            procedure.set_menu_label("Open All Files in Directory...")
            procedure.set_documentation(
                "Opens all supported image files in a selected directory",
                "This plugin allows you to select a directory and automatically "
                "open all supported image files found within that directory. "
                "Supported formats include JPG, PNG, GIF, BMP, TIFF, WebP, PSD, "
                "XCF, SVG, PDF, EPS, and various RAW formats.",
                name
            )
            procedure.set_attribution("GIMP Plugin Developer", "GIMP Plugin Developer", "2024")
            
            # Add the procedure to File menu
            procedure.add_menu_path("<Image>/File/Open")
            
            return procedure
        return None

    def run(self, procedure, run_mode, image, n_drawables, drawables, config, data):
        try:
            # Show directory selection dialog
            directory_path = self.select_directory()
            
            if not directory_path:
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, 
                                                 GLib.Error("No directory selected"))
            
            # Get all image files in directory
            image_files = self.get_image_files(directory_path)
            
            if not image_files:
                Gimp.message(f"No supported image files found in: {directory_path}")
                return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
            
            # Open each image file
            opened_count = 0
            failed_files = []
            
            for file_path in image_files:
                try:
                    # Create GFile object
                    file = Gio.File.new_for_path(file_path)
                    
                    # Load the image
                    loaded_image = Gimp.file_load(run_mode, file)
                    
                    if loaded_image:
                        # Display the image
                        display = Gimp.Display.new(loaded_image)
                        opened_count += 1
                    else:
                        failed_files.append(os.path.basename(file_path))
                        
                except Exception as e:
                    failed_files.append(f"{os.path.basename(file_path)} ({str(e)})")
            
            # Show results
            message = f"Successfully opened {opened_count} out of {len(image_files)} files"
            if failed_files:
                message += f"\nFailed to open: {', '.join(failed_files[:5])}"
                if len(failed_files) > 5:
                    message += f" and {len(failed_files) - 5} more..."
            
            Gimp.message(message)
            
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
            
        except Exception as e:
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, 
                                             GLib.Error(f"Plugin error: {str(e)}"))

    def select_directory(self):
        """Show a directory selection dialog and return the selected path"""
        try:
            # Create a file chooser dialog for directories
            dialog = Gimp.Dialog(use_header_bar=True,
                               title="Select Directory to Open Files From")
            
            dialog.add_button("_Cancel", Gimp.ResponseType.CANCEL)
            dialog.add_button("_Open", Gimp.ResponseType.OK)
            
            # Create file chooser widget
            chooser = Gimp.FileChooserWidget.new(Gimp.FileChooserAction.SELECT_FOLDER)
            
            # Set initial directory to user's home or current directory
            home_dir = os.path.expanduser("~")
            if os.path.exists(home_dir):
                chooser.set_current_folder(Gio.File.new_for_path(home_dir))
            
            dialog.get_content_area().add(chooser)
            dialog.show_all()
            
            response = dialog.run()
            
            if response == Gimp.ResponseType.OK:
                selected_file = chooser.get_file()
                if selected_file:
                    directory_path = selected_file.get_path()
                    dialog.destroy()
                    return directory_path
            
            dialog.destroy()
            return None
            
        except Exception as e:
            # Fallback: use a simple input dialog
            Gimp.message(f"Could not create directory dialog: {str(e)}\n"
                        "Please enter the directory path manually.")
            return None

    def get_image_files(self, directory_path):
        """Get list of all supported image files in the directory"""
        image_files = []
        
        try:
            if not os.path.isdir(directory_path):
                return image_files
            
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                
                # Skip directories and hidden files
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    # Check file extension
                    _, ext = os.path.splitext(filename.lower())
                    if ext in SUPPORTED_EXTENSIONS:
                        image_files.append(file_path)
            
            # Sort files alphabetically
            image_files.sort()
            
        except Exception as e:
            Gimp.message(f"Error reading directory: {str(e)}")
        
        return image_files

# Register the plugin
Gimp.main(BatchFileOpener.__gtype__, sys.argv)
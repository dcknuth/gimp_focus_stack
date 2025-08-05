#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, GObject, Gtk, Gio

import sys, os, subprocess, uuid
DEBUG = 4
user_appdata = os.environ.get('APPDATA')
user_home = str(os.path.expanduser("~"))
tmp_file = ''.join([user_appdata, r"\\GIMP\\3.0\\tmp\\",
                    f'tmp-{uuid.uuid4().hex}.jpg'])
exe_name = "focus-stack.exe"
EXE_PATH = ''.join([user_appdata, r"\\GIMP\\3.0\\scripts\\focus-stack\\",
                    exe_name])
OPTIONS = ['--global-align', '--align-keep-size']

class FocusStack(Gimp.PlugIn):
    # Plugin properties
    __gproperties__ = {
        "name": (str, "Name", "The name of the plugin", "Focus Stack", GObject.ParamFlags.READWRITE),
    }

    def __init__(self):
        super().__init__()

    def do_query_procedures(self):
        # Register the procedure
        return ["plug-in-focus-stack"]

    def do_create_procedure(self, name):
        if name == "plug-in-focus-stack":
            procedure = Gimp.ImageProcedure.new(
                self, name, 
                Gimp.PDBProcType.PLUGIN,
                self.run, None
            )
            
            # Always available, even without open images
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.ALWAYS)
            procedure.set_menu_label("Focus Stack...")
            # Place in main File menu, accessible without open images
            procedure.add_menu_path('<Image>/File/[Open]')
            
            procedure.set_documentation(
                "Opens images to create a new image with greater depth of field",
                "This plugin opens a file selection dialog to choose a directory with images to merge",
                name
            )
            
            procedure.set_attribution("David Knuth", "David Knuth", "2025")
            
            if (DEBUG > 4):
                Gimp.message("Finished creating procedure")
            return procedure
        
        return None

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if (DEBUG > 4):
            Gimp.message("Running plugin now...")
        # Create and show the file selection dialog
        if run_mode == Gimp.RunMode.INTERACTIVE:
            if (DEBUG > 4):
                Gimp.message("Running in interactive mode")
            
            files_dir = self.select_directory()
            if (DEBUG > 4):
                Gimp.message(f"Directory selected is {files_dir}")
            
            if files_dir:
                if (DEBUG > 4):
                    Gimp.message("We can now combine the images")
                self.process_selected_images(files_dir)
                return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
            else:
                # User cancelled or no files selected
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

    def select_directory(self):
        """Show a directory selection dialog and return the selected path"""
        try:
            dialog = Gtk.FileChooserDialog(
                title="Select Directory to Open Files From",
                action=Gtk.FileChooserAction.SELECT_FOLDER)
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            
            # Set initial directory
            home_dir = os.path.expanduser("~")
            if os.path.exists(home_dir):
                dialog.set_current_folder(home_dir)
            
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                directory_path = dialog.get_filename()
                dialog.destroy()
                if(DEBUG > 4):
                    Gimp.message(f"Selected directory: {directory_path}")
                return directory_path
        except Exception as gtk_error:
            Gimp.message(
                "Could not create directory selection dialog.\n"
                f"Error: {str(gtk_error)}")
            return None
    
    def process_selected_images(self, dir_path):
        """Process the image files"""
        # Get a list of all files in the directory (full paths)
        files = [str(os.path.join(dir_path, f))
             for f in os.listdir(dir_path)
             if os.path.isfile(os.path.join(dir_path, f))]
        print(f"Selected {len(files)} files:")
        
        # Do the actual stack with an external call
        command = [EXE_PATH, f'--output={tmp_file}'] + OPTIONS + files
        result = subprocess.run(command)
        if result.returncode < 0:
            Gimp.message(f"Error running the stack command: {result.returncode}")
        else:
            # Open the merged image in GIMP
            try:
                # Load the image
                image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, 
                                     Gio.File.new_for_path(tmp_file))
                
                # Display the image
                display = Gimp.Display.new(image)
                
                # delete the temporary file
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
                
            except Exception as e:
                print(f"Error opening {tmp_file}: {str(e)}")
        if (DEBUG > 4):
            Gimp.message("Processing done")

# Register the plugin
Gimp.main(FocusStack.__gtype__, sys.argv)
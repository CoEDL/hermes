# Using Hermes to Create Resources <img src="../src/img/icon-5-256.png" align="right"/>

## Creating Resources from an ELAN (*.eaf) File

1. Launch Hermes and select the 'Import ELAN File' mode button.
2. Click the 'Load' button and use the file window that opens to select the 
ELAN file you would like to create resources from.
3. Hermes will automatically parse the ELAN file and provide you with a selection
of tiers from which to choose your transcription and translation tiers. When you
are satisfied with your selection, click the import button.
4. A table will appear, populated with the transcriptions, translations and buttons
for previewing audio.
    - If you would like re-record audio for any transcription, right-click the preview
    button for that line, a recording window will appear. You can change the recording
    microphone in the Settings/Preferences Menu (⌘ + B).
    - If you would like to associate an image with a transcription, left-click the image
    icon.
    - Transcription and translation text is editable and can be changed before exporting.
5. Click the appropriate 'Include' checkboxes for any transcriptions you would like to 
include in the exported resources. You can also click the 'Select All' button.
6. When you have selected all of the transcriptions you require, click the 'Choose' button
to select an output location.
7. Once you have selected a valid output location an export button should appear. Click it
to begin the export process.
    -  If you want to change the output format (OPIE, JSON, CSV), you may do so in the
    Settings/Preferences menu, which is accessible from the toolbar or via (⌘ + B).
    -  Exporting to the LMF (JSON) format will prompt you for additional information about the
    transcription and translation languages, as well as the resource author.
    
<p align="center">
<img src="img/elan-example.gif" width="590"/>
</p>
    
## Creating Resources from Scratch
1. Launch Hermes and select the 'Start From Scratch' mode button.
2. Input transcriptions and translations as required.
    - New rows for transcriptions/translations can be added by clicking the 'Add Row'
    button, through the toolbar's 'Table' meny or by using the shortcut (⌘ + N).
    - You can record audio for each transcription by left or right-clicking the button
    in the 'Preview' column, which will open the recording window.
    - Images can be associated with each transcription by clicking the button in the 
    'Image' Column
3. Click the appropriate 'Include' checkboxes for any transcriptions you would like to 
include in the exported resources. You can also click the 'Select All' button.
4. When you have selected all of the transcriptions you require, click the 'Choose' button
to select an output location.
5. Once you have selected a valid output location an export button should appear. Click it
to begin the export process.
    -  If you want to change the output format (OPIE, JSON, CSV), you may do so in the
    Settings/Preferences menu, which is accessible from the toolbar or via (⌘ + B).
    -  Exporting to the LMF (JSON) format will prompt you for additional information about the
    transcription and translation languages, as well as the resource author.
    
<p align="center">
<img src="img/scratch-example.gif" width="590"/>
</p>

### Note: Installing the FFMPEG Plugin
- By default, Hermes only includes support for WAV audio.
If you need to work with other formats, please install the FFMPEG plugin
in the settings menu.
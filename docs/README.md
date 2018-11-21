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

## Saving your Progress
1. Click on 'File' in the menu toolbar.
2. Click on 'Save As' if you have not already saved previously.
    - Clicking on 'Save' will also start the 'Save As' function, otherwise you can use 'Save'
    over the current file.
3. In the save dialogue window, choose a folder to place your save file.
4. Name your save file and hit the 'Save' button.
5. If you haven't already chosen an export location, Hermes will now prompt you to choose or make
a location to export your image and audio assets to.
    - Note, we recommend making a separate folder for your save assets to your usual export location.
    (See creating resources above).
6. A window will open for you to enter language and authorship details for your save file.
7. Hermes will now have created a save file according to your specifications which can be loaded by any
copy of Hermes.

## Opening a previous saved file
1. Ensure that the Hermes transcription table is visible (either from an ELAN import or Starting from Scratch, see guides).
2. Click on 'File' in the menu toolbar.
3. Click on 'Open', and a open file dialogue window will now open for you to navigate your systems file
structure.
4. Locate where you saved a previous file (.hermes extension), and click the Open button in the window.
5. The table will now be populated with the files data.

## Creating Templates
1. Fill in the hermes table either through importing an ELAN file or starting from scratch.
2. Click on Templates in the menu toolbar.
3. Click on Create Template.
4. Tick the checkbox to indicate which columns (Either Transcription, or Translation) you want to use
for the template. You may choose both if relevant.
5. Save the template file. The template file can be loaded by hermes to automatically populate word
columns to allow for custom audio recording and image attachments per word list.
    - Note you may be asked to input language and authorship information during the save process.

## Loading Templates
1. Ensure that the Hermes transcription table is visible.
2. Click on 'Templates' in the menu toolbar.
3. Click on Load Template, and select the appropriate template (.htemp) file to load.
4. Hermes will automatically populate the table based on this file, ready for you to attach images and
record audio for the word list.

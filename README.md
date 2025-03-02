![REAssetLibraryTitle](https://github.com/user-attachments/assets/a5bd7edf-1c64-441b-ae40-f88abfea38f7)


**V0.6 (2/28/2025)** | [Change Log](https://github.com/NSACloud/RE-Asset-Library?tab=readme-ov-file#change-log) | [FAQ](https://github.com/NSACloud/RE-Asset-Library/tree/main?tab=readme-ov-file#faq)

**BETA RELEASE, THERE MAY BE BUGS**

This Blender addon adds the ability to browse through RE Engine models and other files inside the asset browser.
### [Download RE Asset Library](https://github.com/NSACloud/RE-Asset-Library/archive/refs/heads/main.zip)

**Video Guide**

[![RE Asset Library Yotube Video Guide](https://github.com/user-attachments/assets/9799239b-e676-42e6-83fe-3679ac1d2103)](https://www.youtube.com/watch?v=jLM3wbEFANg)

## Features
 - Game files can be extracted automatically as assets are imported.
 - RE Engine assets can be assigned names, categories and tags to make searching for them easier.
 - Asset libraries can be downloaded directly in Blender through the addon.
 - Users can submit the changes they make to names, categories and tags to be included in a future update.
 - New asset libraries can be created by providing an RE Tool list file.

## File Extraction

This addon allows for files to be unpacked from the game's chunk files as they're imported. Meaning you don't have to waste dozens of gigabytes on files you don't need.

![image](https://github.com/user-attachments/assets/99fbce1f-3281-4c7d-8f8f-d619b1cd438b)

It also supports selective extraction, so you can extract all files of a certain category or only extract certain pak files.

No list file is required, just download an asset libary, set the path to the game's exe file and extract.

In addition, this tool is extremely fast at extracting files compared to all of the other tools.

### Performance Benchmarks

This tool puts all other pak extraction tools to shame in terms of speed.

**Pak Extraction Times**

* RETool - 24m:05s (Written in C++)
* ree-unpacker - 4m:51s (Written in C#)
* ree-pak-cli - 2m:19s (Written in Rust)
* RE Asset Library - 1m:06s (Written in Python)

Test run on Monster Hunter Rise's re_chunk_000.pak. (42.8 GB, 158,791 Files)

Specs: Ryzen 5 5600x, Writing from Samsung 980 SSD to Samsung 970 EVO SSD.

This tool scales very well with hard drive and CPU speeds.

It could run even faster with a better CPU and hard drive, as the usage for both was hitting their max.

## Planned Future Updates
 - Support for more file formats, such as animations.


## Requirements

**This addon is reliant on new features of the Blender API, versions before 4.3.2 are not supported.**
* [Blender 4.3.2 or higher](https://www.blender.org/download/)
* [RE Mesh Editor](https://github.com/NSACloud/RE-Mesh-Editor) - Blender addon for importing RE Engine models.
* [RE Chain Editor](https://github.com/NSACloud/RE-Chain-Editor) - Blender addon for setting up bone physics. This is required if you are going to import chain files through the asset library.

## Supported Games
 Supports all games that are supported by RE Mesh Editor.

 [Asset Library Collection Repository](https://github.com/NSACloud/RE-Asset-Library-Collection?tab=readme-ov-file#current-library-status)

 More libraries will be added to the repository in the future.


## Installation
Download the addon from the "Download RE Asset Library" link at the top or click Code > Download Zip.

In Blender, go to Edit > Preferences > Addons, then click "Install" in the top right.

The install button is found by clicking the arrow in the top right of the addon menu.

![image](https://github.com/user-attachments/assets/49dd95c1-9a20-49d8-af55-7160d54836df)

Navigate to the downloaded zip file for this addon and click "Install Addon". The addon should then be usable.

To update this addon, navigate to Preferences > Add-ons > RE Asset Library and press the "Check for update" button.



## Downloading Asset Libraries

To download asset libraries, use the "Download RE Asset Libraries" button in the addon preferences.

![image](https://github.com/user-attachments/assets/4e50f9f1-83f1-41fb-9c84-1b60c860c641)

A window will be shown. You can choose which game to download the asset library for from the drop down menu at the top.

![image](https://github.com/user-attachments/assets/ce165494-863d-4b03-887c-780e5ef07050)

After clicking download, a new blend file will be opened and thumbnails will be assigned to files.

This can take a minute for the first time depending on the speed of your PC and size of the library.

Once it finishes, you can close the new blend file that opened.

Now you can access that library via the Asset Browser in any blend file.

> [!TIP]
> Setting up an Asset Browser workspace and saving it to the startup file can save time with setting up. See below.

<details>
  <summary>Setting Up An Asset Browser Workspace</summary>

Blender (as of 4.3.2) doesn't include an asset browser workspace. You can create one however.

Start by opening a new blend file. Click the new workspace button (+ sign) on the bar at the top, choose Duplicate Current.

Double click the new tab and rename it to RE Assets (or whatever you want).

![image](https://github.com/user-attachments/assets/bd8d9355-1073-4ae5-a01f-90f1d28df034)

Drag a corner of the viewport to create a new window. Set the type to Asset Browser.

![image](https://github.com/user-attachments/assets/a6d8db2b-c4ac-4c04-b7ea-1bfa445796a5)

Change back to the Layout workspace and click File > Defaults > Save Startup File.

![image](https://github.com/user-attachments/assets/0185b946-eea0-4c94-9497-d02034653f22)


Now whenever you open a new blend file, you can click the RE Assets tab at the top to skip having to set up the asset browser.

 </details>

## Set Chunk Paths

This addon uses the chunk paths set in the RE Mesh Editor addon preferences to search for files.

This is usually set automatically when a mesh file is imported from an extracted pak file.

![image](https://github.com/user-attachments/assets/ead76cee-37ac-4e87-92c3-3386feffb2b2)

If the path for your game is not set, add a new chunk path for it.
Choose the game and set the path to the natives\STM\ folder. (See above for reference)

## FAQ

* **Only an Empty axis object appears when dragging an asset from the asset browser.**

> This is likely because you're dragging an asset in from the browser into the asset library blend file.
> 
> Due to Blender limitations and the way this addon functions, you can't drag assets into the asset library blend file.
> 
> You can only import assets while in a different blend file.
> 
> (So in short: Don't drag things from the asset browser in REAssetLibrary_XXXX.blend)


* **Why are libraries much bigger when installed?**

> Asset libraries after installation can reach sizes of around 2 GB each depending on the game. This is because they are compressed when downloaded.
> 
> Additionally, they must be packed into .blend files for Blender to use. The majority of the space used comes from images.
> 
> Blender creates a duplicate of each image and packs it into the blend file to use for asset thumbnails. This unfortunately isn't very space efficient.


* **Why do some files show up white?**

> This means the material file for that model wasn't found when it was rendered.
> 
> Some models use non standard paths for material files, the mesh editor needs to be updated to account for these variations in file paths.
> 
> These thumbnails may be corrected in a future update.
> 
* **The materials on a model don't look right.**

> RE Mesh Editor has to account for every single RE Engine game released.
> 
> There are many variations in material setups across RE games and making it work perfectly in all of them is difficult.
> 
> This will be fixed over time as I make updates.

**For additional help, go here:**

[Monster Hunter Modding Discord](https://discord.gg/gJwMdhK)

[Modding Haven Discord](https://discord.gg/modding-haven-718224210270617702)

# NO GAME ASSETS ARE INCLUDED WITH THIS ADDON
**This addon and any downloaded asset libraries do not contain any game assets. You must own the games and have them installed.**


The way asset libraries with this addon works is very simple.

Asset libraries downloaded by this addon only contain the following things:
* The path to where a file can be found.
* The names, categories and tags associated with that file.
* A rendered preview image of said file.
* Additional metadata required for importing the library to Blender.

When an asset is dragged from the asset browser, the addon will search through the extracted game files on the user's system.

If the file is present on the system, it will be imported by an addon associated with that file.


## Change Log

### V0.9 - 2/28/2025
* Added support for extracting HD textures from the MH Wilds HD texture pack.

Note that if you have already extracted files, in order to be able to extract HD textures, you have to do the following things:

In the asset library blend file (REAssetLibrary_MHWILDS.blend), click the "Reload Pak Cache" button.

If there's already a model you've extracted before and you want the higher quality textures, use the Configure RE Asset settings button in the asset browser and enable "Force Extract Files".

Additionally, check the "Reload Cached Textures" box when importing the mesh file.

### V0.8 - 2/28/2025
* Added error message to tell that RE Mesh Editor is not installed.
* Minor bug fixes.

### V0.7 - 2/28/2025
* Fixed issue where reading paks would fail on MH Wilds if the HD texture pack is installed.

### V0.6 - 2/28/2025
* Thumbnails now use lossy compression, reducing the download sizes of each library by roughly 50%.

All libraries have been updated to use compressed thumbnails.

* Fixed issues with filepaths when extracting files on Linux.
* Added Force Extract Files setting, this makes it so files will always be extracted when imported, rather than reading already extracted ones.
* Other minor bug fixes.

### V0.5 - 2/22/2025
* Added pak extraction capabilities. 

Files can now be extracted from the pak by dragging assets from the asset browser into Blender.

Additionally, pak files can be selectively extracted using the Extract Game Files button inside an asset library blend file.

* Minor bug fixes. 

### V0.4 - 2/9/2025
* Fixed issue where Blender would make paths relative.
* An error message will appear if a file is not found at any of the provided chunk paths.

### V0.3 - 2/9/2025
* Changed HDRI used for rendering asset thumbnails.
* Improved quality of rendered thumbnails.
* Added configurable options at the top of Resources\Scripts\renderAssets.py.

### V0.2 - 2/6/2025
* Fixed issue where thumbnails would not update when using the Check For Library Update button.
* Check For Library Update no longer opens a new Blender window.

Note: If you have an issue where assets in the browser show up as gray file icons, use the "Fetch RE Asset Thumbnails" button and check "Force Reload All".

This button can be found in the 3D view on the N panel under the "RE Assets" tab when you have an asset library blend file open.

### V0.1 - 1/18/2025
* Experimental release.
  

## Credits

- [Ekey](https://github.com/Ekey/) - Used RE Pak Tool as a reference for pak structure
- [CG Cookie](https://github.com/CGCookie) - Addon updater module

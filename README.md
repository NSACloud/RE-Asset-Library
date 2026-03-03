
![REAssetLibraryTitle](https://github.com/user-attachments/assets/a5bd7edf-1c64-441b-ae40-f88abfea38f7)


**V0.24 (3/2/2026) | [Change Log](https://github.com/NSACloud/RE-Asset-Library?tab=readme-ov-file#change-log) | [FAQ](https://github.com/NSACloud/RE-Asset-Library/tree/main?tab=readme-ov-file#faq)**

---
**BETA RELEASE, THERE MAY BE BUGS**

This Blender addon adds the ability to browse through RE Engine models and other files inside the asset browser.
### [Download RE Asset Library](https://github.com/NSACloud/RE-Asset-Library/archive/refs/heads/main.zip)

<img width="1551" height="903" alt="image" src="https://github.com/user-attachments/assets/230e4476-9bca-4e50-b32b-ac6e4b9b1ddb" />

## Installation/Usage Instructions (2026)
**The video guide below is outdated.** I will be making a new tutorial soon showing the install/setup process.

For now, follow the written instructions below.

Make sure you have [Blender 4.3.2 or higher](https://www.blender.org/download/).

Download the addon from the **Download RE Asset Library** link at the top or **click Code > Download Zip**.

Download [RE Mesh Editor](https://github.com/NSACloud/RE-Mesh-Editor) and [RE Chain Editor](https://github.com/NSACloud/RE-Chain-Editor) also.

In Blender, go to Edit > Preferences > Addons, then click the arrow in the top right of the addon menu and choose **Install From Disk**.

<img width="877" height="321" alt="image" src="https://github.com/user-attachments/assets/60a4e041-30fe-4d34-a1f8-33b9634fef14" />

Navigate to the downloaded zip file for each addon and click **Install Addon**. Be sure to check the box next to each addon after installing. The addon should then be usable.

To download asset libraries, use the **Download RE Asset Libraries** button in the addon preferences under RE Asset Library.

<img width="878" height="356" alt="image" src="https://github.com/user-attachments/assets/592ecb9c-e359-4d1e-83bc-ef123e641080" />

A window will be shown. You can choose which game to download the asset library for from the drop down menu at the top.

![image](https://github.com/user-attachments/assets/ce165494-863d-4b03-887c-780e5ef07050)

After clicking download, a new blend file will be opened and thumbnails will be assigned to files.

This can take a minute for the first time depending on the speed of your PC and size of the library.

Once it finishes, you can access the asset library from the asset browser. If it doesn't show up, try restarting Blender.

To open the asset browser, click **File > New > RE Assets**.

In the asset browser in the bottom half of the screen, change the library from **All Libraries** to whichever asset library you downloaded.

<img width="644" height="369" alt="image" src="https://github.com/user-attachments/assets/a80126a4-f3f2-495c-ba8e-e35def702405" />


Open the **RE Asset Library** menu and click **Set Game Extract Paths**. Set **Game EXE File Path** to the main .exe file for your game. 

You can find it in Steam by right clicking the game > **Manage** > **Browse Local Files.**

<img width="1417" height="425" alt="image" src="https://github.com/user-attachments/assets/1f9d6bc3-6a30-4cc8-8e3a-6af203a8625b" />

Once you press OK, everything will be set up and you can drag models in from the asset browser to import them.

<img width="1281" height="902" alt="image" src="https://github.com/user-attachments/assets/eef2c71e-7aa5-40eb-a32a-5d645a440cdb" />

If you want to extract game files other than models, open the RE Asset Library menu in the asset browser and choose **Extract Game Files**.

> [!TIP]
> If you don't want to extract the whole game, extracting only **Model Related Files**, **Prefab Files** and **User Files** is usually enough for most modding purposes. 

<img width="1301" height="604" alt="image" src="https://github.com/user-attachments/assets/bc19ed63-dee2-426d-9da3-3d93f1803ccf" />

### Updating the Addon and Asset Libraries

To update this addon, navigate to Preferences > Add-ons > RE Asset Library and press the "Check for update" button.

To update asset libraries for each game, select the asset library in the asset browser and click the "Check For Library Update" button in the "RE Asset Library" menu.
<details>
<summary>Video Guide - OUTDATED</summary>
 
[![RE Asset Library Yotube Video Guide](https://github.com/user-attachments/assets/9799239b-e676-42e6-83fe-3679ac1d2103)](https://www.youtube.com/watch?v=jLM3wbEFANg)
</details>

## Features
 - Game files can be extracted automatically as assets are imported.
 - RE Engine assets can be assigned names, categories and tags to make searching for them easier.
 - Asset libraries can be downloaded directly in Blender through the addon.
 - Users can submit the changes they make to names, categories and tags to be included in a future update.
 - New asset libraries can be created by providing an RE Tool list file.

## Requirements

**This addon is reliant on new features of the Blender API, versions before 4.3.2 are not supported.**
* [Blender 4.3.2 or higher](https://www.blender.org/download/)
* [RE Mesh Editor](https://github.com/NSACloud/RE-Mesh-Editor) - Blender addon for importing RE Engine models.
* [RE Chain Editor](https://github.com/NSACloud/RE-Chain-Editor) - Blender addon for setting up bone physics. This is required if you are going to import chain files through the asset library.

## Supported Games
 Supports all games that are supported by RE Mesh Editor.

 [Asset Library Collection Repository](https://github.com/NSACloud/RE-Asset-Library-Collection?tab=readme-ov-file#current-library-status)


## FAQ

* **Models appear red when imported.**

> This means you're missing textures. Enable the "Force Extract Files" option in the RE Asset Library menu inside the asset browser.
> 
> Drag the asset onto the 3D view again. Any missing files will be extracted automatically.

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

* **Why do some files not have thumbnails?**

> Certain files may show as "MESH" in the library. These are usually meshlet based models.
>
> Support for these models is not yet complete and they don't import properly. Therefore making renders of these is skipped. 


**For additional help, go here:**

[RE Engine Modding Wiki](https://github.com/Havens-Night/REEngine-Modding-Documentation)

[Monster Hunter Modding Discord](https://discord.gg/gJwMdhK)

[Haven's Night Discord](https://discord.gg/modding-haven-718224210270617702)

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

### V0.24 - 3/2/2026
* Fixed missing refskel and skeleton icons.

### V0.23 - 3/2/2026
* Fixed issue with extracting DLC paks in RE9.
* When the addon is updated, saved pak caches will be reloaded automatically.
* Added refskel and skeleton import support.
* Minor bug fixes.

### V0.22 - 2/27/2026
* Fixed issue with Force Extract Files on RE9.

### V0.21 - 2/27/2026
* Added Resident Evil 9 support.
* Simplified the Extract Game Files window. It now lets you pick specific types of files to extract.
* Extract Game Files now shows the amount of space required to extract the selected files.
* Force Extract Files is now enabled by default. This is to avoid issues if only the meshes are extracted.

### V0.20 - 2/18/2026
* Fixed issues with the MDF updater on the latest MH Wilds update.
* Reworked patch pak creation to be faster and use much less memory.
* Added compression to newly created patch pak files.
* Improved compatibility with mod patch paks created by RETool.
* Improved speed of file extraction when dragging assets from the asset browser.
* Minor bug fixes.

### V0.19 - 2/11/2026
* Added support for Monster Hunter Stories 3.
(Side note: The Monster Hunter Rise asset library is updated and fully labeled now.)
* Made hashing approximately 20x faster, this makes unpacking pak files take less time.
* Fixed issue where audio files wouldn't extract correctly in Pragmata and Monster Hunter Stories 3. NOTE: There is currently an issue with extracting .mov (video files) with these games. This will be fixed at a later point.
* Added Generate Material Compedium and Generate CRC Compendium buttons in asset libraries. These allow an asset library to use the CRC and MDF updaters.
* Other minor fixes.

### V0.18 - 12/15/2025
* Added support for Pragmata.
* Fixed issue where under certain circumstances, an installed asset library may not show up in the browser.
* Greatly improved the speed of the MDF updater.
* Updated structure of exported MDF files to be identical to vanilla files.
* If the MDF updater is run without the game extract paths being set, it will now prompt to set them.
* Minor bug fixes.

### V0.17 - 10/26/2025
* Added support for unpacking mod pak files. Mod paks can be fully extracted and repacked even if they're using custom file paths.
* Mod pak files can be extracted by dragging them onto the 3D view or by using the Extract Mod Pak button in the RE Mesh tab.
* Added Batch RSZ CRC Updater button. This allows for the CRC values in user, pfb and scn files to be updated to allow a file to continue to work after a game update.
This is experimental and may not work if there's been structural changes to files after an update.
Only the SF6 library supports this feature at the moment, MH Wilds support will be added upon the next major game update.


### V0.16 - 8/27/2025
* Added FBXSkel importing support to asset libaries.
The latest version of RE Mesh Editor is required to import them.
* Fixed issue where an error would occur when attempting to read empty pak files on RE2RT.


### V0.15 - 8/14/2025
* Fixed some issues with the MDF updater.


### V0.14 - 8/13/2025
* Added MDF updater functionality.
This allows for outdated MDF (material) files to be updated easily with a click of a button.
The MDF updater buttons can be found in the RE MDF tab under the RE Asset Extensions tab.


### V0.13 - 6/1/2025
* Added RE Assets workspace. It can be accessed using File > New > RE Assets
* Asset library options are now accessible from the asset browser by opening the RE Asset Library menu.

![image](https://github.com/user-attachments/assets/4db801db-964d-4567-a469-92a481ab03e0)

This allows for extracting of game files and updating asset libraries directly from the asset browser.

* Added Onimusha 2 support.
* Fixed issue where having certain characters in a file path could cause files to not be found.
* Set Game Extract Paths will now remember the last chosen path.
* Set Game Extract Paths will now warn if the extracted files path is too long and may cause issues with path length.
* Mod pak files are now ignored when extracting files (MH Wilds only).
* Corrected pak load order to load DLC last.
* Minor bug fixes.

### V0.12 - 3/18/2025
* Fixed issue where assets couldn't be imported if the blend file was saved to the same drive that the asset library is saved to.

### V0.11 - 3/17/2025
* Fixed path related issues that would cause assets not to import on certain systems.
* Excluded unrelated file types from being packed into pak files.
* The console will now be shown while creating a patch pak.

### V0.10 - 3/7/2025
* Added patch pak creation tools. These are required (for now at least) for textures to work for MH Wilds.

You can create a patch pak by using the "Create Patch Pak" button in the RE MDF tab in the 3D view.

They can be installed using Fluffy Manager.

Be sure to update to the latest version of RE Mesh Editor or the button won't show up.

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

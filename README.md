# StoryTable Beta Testing

This repository provides StoryTable beta installers for invited testers.
StoryTable's application source remains private.

## Current public tester builds

The platform versions are listed separately because the Windows and macOS
release pipelines are currently at different checkpoints.

Choose the download that matches your computer:

<!-- BEGIN CURRENT DOWNLOADS -->
- **Windows - 0.1.133:** [Download StoryTable for Windows](https://github.com/framedbyrandy/storytable-testers/releases/download/v0.1.133-beta/StoryTable-0.1.133-Windows-Setup.exe)
- **Mac with an Apple M-series chip - 0.1.119:** [Download StoryTable for Apple Silicon](https://github.com/framedbyrandy/storytable-testers/releases/download/v0.1.119-beta/StoryTable-0.1.119-macOS-Apple-Silicon.dmg)
- **Mac with an Intel processor - 0.1.99:** [Download StoryTable for Intel Mac](https://github.com/framedbyrandy/storytable-testers/releases/download/v0.1.99-beta/StoryTable-0.1.99-macOS-Intel.dmg)
<!-- END CURRENT DOWNLOADS -->

These builds connect to StoryTable's staging service. Do not use them for
production customer work.

Release history and checksums are available on the
[Releases page](https://github.com/framedbyrandy/storytable-testers/releases).

## Platform security notes

- **Windows:** Windows may display "Windows protected your PC." Select
  **More info**, verify that the file came from this repository, and choose
  **Run anyway**. Some managed computers may block unsigned applications.
- **macOS:** The current Mac packages are signed with Developer ID, notarized
  by Apple, and stapled. Open the DMG and drag StoryTable to Applications.

## Reporting feedback

Please include the operating-system version and architecture, what you
clicked, what you expected, what happened, and a screenshot for visual or
error issues.

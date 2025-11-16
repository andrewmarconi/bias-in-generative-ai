# TUI Spec

## Main (Home) Screen

- Shows the status of the current experiment (real-time)
  - Sidebar showing a list of past experiments.
  - If an experiment is active, its status shows in the main body area.
  - if an experiment is NOT active, then the config screen shows in order to instantiate a new experiment.
  - There are these steps in the experiment process:
    - 1. Setup / Config. Tabbed interface. All the current config options.
    - 2. Image Generation. Shows the active steps, grouped by prompt type (occupational, contextual, neutral -- as they're listed in the config), and then by image generation task (two levels of progress bars).
    - 3. VQA Analysis. Shows the active steps, grouped by bias categories and then within each, a progress bar showing the number of images processed.
    - 4. Statistical Analysis. Shows the active steps in this analysis.
  - **Metadata Modal** (with tabs). Can be viewed whilst experiment is running (without stopping the experiment). Shows: Generation, Prompts, VQA Analysis, and Statistics. (hotkey: ctrl-m)

## Global Modals
    - **Help** as exists. (hotkey: ctrl-h)
    - **Palette** as exists. (hotkey: ctrl-p)

## History Details
  - If user clicks on one of the history items on Main, they are taken to a screen to view the data from a historic run.
  
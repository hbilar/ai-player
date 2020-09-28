# ai-player

This is the git-repo for my MSc Advanced Computer Science project.

The TLDR; is:
Python 'player' that plays Supermario, by employing TensorFlow object
detection techniques. Object locations are then fed into a little neural
network (self developed by myself in pure Python), which outputs game
play decisions.

The NES game itself runs in a modified version of the LaiNES emulator.
The modifications were necessary for the Python player to be able to
receive game play images over TCP, and also send game play instructions
to the emulator (again, over TCP).


In order to not duplicate information, the best bet is probably to read
the project report in the first instance. [project_report_word-format.docx](project_report_word-format.docx)


## Other relevant repos

The modified version of the LaiNES emulator (with TCP support) can be found
here: [LaiNES-with-tcp](https://github.com/hbilar/LaiNES-with-tcp)

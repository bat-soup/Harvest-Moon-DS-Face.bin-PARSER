# Harvest-Moon-DS-Face.bin-PARSER
A parser for Harvest Moon DS's face.bin file. This should work for all versions of Harvest Moon DS including Harvest Moon DS: Cute

**How it works**
HMDS's face.bin file contains all of the character portraits in the game, except for the channel sprites (still looking to find them!)
The structure of the file goes as follows:
1. Pointer table with entries that reference each character (HMDS:Cute has 107 characters in this file, thus there are 107 entries in the pointer table. However, HMDS Legacy has less "characters", because Skye and the Daughters are not included.)
2. Going to each character entry you see....
  a. two 16-color palettes used by the character.
  b. an 18-entry long sub-pointer table that is referencing the 6 "expressions" used by each character. Each "expression" has 3 pointers each, which lead to 1) the lz77 compressed graphics data, 2) the raw DS OAM metadata, and 3) Seemingly random and unused, points to totally random things as far as it seems.

3. If a character has less than 6 expressions (i.e: they are not marriagable, the player character, or your child), the missing expressions will instead point to Da-Chan, interestingly.

^^^ Da-chan only has 3 expressions himself, but the remaining expressions are some unused Da-Chan graphics.


This program will parse all of the data into a directory with a folder for each character that will include .bin files for the character's 2 palettes, and .bin files each expression's uncompressed graphics and their respective OAM data.

This can be used in tandem with my HMDS Portrait reconstructor!

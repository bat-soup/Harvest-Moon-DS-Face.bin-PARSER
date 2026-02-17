
"""
Smart face.bin Parser
Extracts portraits from face.bin -- Removes all da-chan
"""

import struct
import os



# Character names are inconsistent across versions, got rid of them: if you still want to use them, they work for HMDS:Cute
# CHARACTER_NAMES = [
#     "Claire", "Celia", "Muffy", "Nami", "Romana", "Sebastian", "Lumina", "Wally",
#     "Chris", "Grant", "Kate", "KateOlder", "Hugh", "HughOlder", "Carter", "Flora",
#     "Vesta", "Marlin", "Ruby", "Rock", "Hardy", "Galen", "Nina", "Daryll",
#     "Cody", "Gustafa", "Griffin", "Van", "Kasey", "Patrick", "Murrey", "Takakura",
#     "Mukumuku", "DaChan", "Barney", "Mimi", "Popuri", "Ann", "Karen", "Elli",
#     "Mary", "Kai", "Cliff", "Rick", "Trent", "Gray", "HGoddess", "Thomas",
#     "Gotz", "Gourmet", "SonBabyMuffy", "SonKidMuffy", "SonAdultMuffy", "SonBabyNami",
#     "SonKidNami", "SonAdultNami", "SonBabyCelia", "SonKidCelia", "SonAdultCelia", "SonBabyLumina",
#     "SonKidLumina", "SonAdultLumina", "SonBabyFlora", "SonKidFlora", "SonAdultFlora", "Leia",
#     "Kiera", "WPrincess", "Skye", "SprTeamRedLeader", "SprTeamOrangeLeader", "SprTeamYellowLeader",
#     "SprTeamGreenLeader", "SprTeamIndigoLeader", "SprTeamPurpleLeader", "SprTeamBlueLeader", "SprTeamRed",
#     "SprTeamOrange", "SprTeamYellow", "SprTeamGreen", "SprTeamIndigo", "SprTeamPurple", "SprTeamBlue",
#     "Guts", "Casino1", "Casino2", "Casino3", "Casino4", "Jackie", "Jet",
#     "BabySprite", "Pony", "DaughterBabyRock", "DaughterKidRock", "DaughterAdultRock", "DaughterBabyGustafa",
#     "DaughterKidGustafa", "DaughterAdultGustafa", "DaughterBabyMarlin", "DaughterKidMarlin", "DaughterAdultMarlin",
#     "DaughterBabyGriffin", "DaughterKidGriffin", "DaughterAdultGriffin", "DaughterBabyCarter", "DaughterKidCarter",
#     "DaughterAdultCarter"
# ]

EXPRESSION_NAMES = ["neutral", "happy", "angry", "sad", "love", "hate"]

def decompress_lz77(data, offset):
    """Decompress LZ77 data"""
    if offset >= len(data) or data[offset] != 0x10:
        return None
    
    decompressed_size = struct.unpack_from('<I', data, offset)[0] >> 8
    output = bytearray()
    src_pos = offset + 4
    
    try:
        while len(output) < decompressed_size and src_pos < len(data):
            flags = data[src_pos]
            src_pos += 1
            
            for i in range(8):
                if len(output) >= decompressed_size:
                    break
                if src_pos >= len(data):
                    break
                    
                if flags & 0x80:
                    if src_pos + 1 >= len(data):
                        break
                    info = struct.unpack_from('>H', data, src_pos)[0]
                    src_pos += 2
                    length = ((info >> 12) & 0xF) + 3
                    disp = (info & 0xFFF) + 1
                    for _ in range(length):
                        if len(output) < disp:
                            output.append(0)
                        else:
                            output.append(output[-disp])
                else:
                    output.append(data[src_pos])
                    src_pos += 1
                
                flags <<= 1
    except:
        return None
    
    return bytes(output[:decompressed_size])

def parse_face_bin(face_bin_path, output_dir):
    """Parse face.bin and extract all portraits (Dachan will be removed)"""
    
    with open(face_bin_path, 'rb') as f:
        data = f.read()
    
    print("="*80)
    print("HARVEST MOON DS FACE.BIN PARSER")
    print("="*80)
    print()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    first_pointer = struct.unpack('<I', data[0:4])[0]
    
    # The pointer table is 4 bytes per character
    # So: number of characters = first_pointer / 4
    num_characters = first_pointer // 4
    
    print(f"  First pointer value: 0x{first_pointer:08X} ({first_pointer} bytes)")
    print(f"  Pointer table size: {first_pointer} bytes")
    print(f"  Character count: {num_characters} characters")
    
    # Verify this makes sense
    if num_characters < 1 or num_characters > 500:
        print(f"\n  WARNING: Detected character count ({num_characters}) seems unusual!")
        print(f"  File might be corrupted or in an unexpected format.")
        return
    
    # First, get DaChan's graphics pointers from Claire (character 0)
    # Claire uses DaChan as fallback for ALL her expressions besides neutral, this is perfect to detect the rest of DaChan fallbacks, because
    #all characters have a neutral expression
    print("Step 1: Getting DaChan's expression pointers from Player Character (Claire or Pete)...")
    print("-"*80)
    
    claire_char_offset = first_pointer
    claire_subtable_offset = claire_char_offset + 64
    
    # Get 1-5 of Claire's graphics offsets - these are DaChan's expressions
    dachan_gfx_offsets = []
    for expr_idx in range(1, 6):
        entry_idx = expr_idx * 3
        gfx_ptr_offset = claire_subtable_offset + (entry_idx * 4)
        gfx_offset = struct.unpack('<I', data[gfx_ptr_offset:gfx_ptr_offset+4])[0]
        dachan_gfx_offsets.append(gfx_offset)
        print(f"  DaChan expression {expr_idx}: 0x{gfx_offset:08X}")
    
    print(f"\nDaChan has {len(dachan_gfx_offsets)} expressions used as fallbacks")
    print(f"\nDaChan (character 33) has {len(dachan_gfx_offsets)} expressions that are used as fallbacks by other characters.")
    
    # Now process all  characters
    print("\n" + "="*80)
    print("Step 2: Processing all characters...")
    print("="*80)
    print()
    
    stats = {
        'total_chars': 0,
        'total_expressions': 0,
        'skipped_dachan': 0
    }
    
    for char_id in range(num_characters):
        
        # Read character pointer
        char_ptr_offset = char_id * 4
        char_offset = struct.unpack('<I', data[char_ptr_offset:char_ptr_offset+4])[0]
        
        if char_offset >= len(data):
            continue
        
        # Extract palettes
        palette1 = data[char_offset:char_offset+32]
        palette2 = data[char_offset+32:char_offset+64]
        
        # Read subtable -- subtable contents:
        #18 entry pointer table with this format:
        #   1st pointer: expression 0's compressed graphics ; 2nd pointer: expression 0 OAM metadata; 3rd pointer: ??? (unused by this program, might be unused in the game)
        subtable_offset = char_offset + 64
        
        # Process 6 expressions
        expression_indices = [0, 3, 6, 9, 12, 15]
        expressions_found = []
        
        for expr_num, entry_idx in enumerate(expression_indices):
            # Read graphics pointer
            gfx_ptr_offset = subtable_offset + (entry_idx * 4)
            if gfx_ptr_offset + 3 >= len(data):
                continue
            
            gfx_offset = struct.unpack('<I', data[gfx_ptr_offset:gfx_ptr_offset+4])[0]
            
            # Check if this is a DaChan fallback expression
            # Skip if: (1) This is NOT DaChan himself AND (2) pointer matches a DaChan expression
            is_dachan_fallback = (char_id != 33) and (gfx_offset in dachan_gfx_offsets)
            
            if is_dachan_fallback:
                stats['skipped_dachan'] += 1
                continue
            
            # Read OAM pointer
            oam_ptr_offset = subtable_offset + ((entry_idx + 1) * 4)
            if oam_ptr_offset + 3 >= len(data):
                continue
            
            oam_offset = struct.unpack('<I', data[oam_ptr_offset:oam_ptr_offset+4])[0]
            
            # Try to decompress graphics
            if gfx_offset < len(data):
                graphics = decompress_lz77(data, gfx_offset)
                
                if graphics:
                    # Extract OAM
                    oam_data = None
                    if oam_offset < len(data):
                        meta_size_bytes = data[oam_offset:oam_offset+4]
                        if len(meta_size_bytes) == 4:
                            meta_size = struct.unpack('<I', meta_size_bytes)[0]
                            if 0 < meta_size < 1000 and oam_offset + meta_size <= len(data):
                                oam_data = data[oam_offset:oam_offset+meta_size]
                    
                    expressions_found.append({
                        'num': expr_num,
                        'name': EXPRESSION_NAMES[expr_num],
                        'graphics': graphics,
                        'oam': oam_data
                    })
        
        # Save character if they have at least one real expression
        if expressions_found:
            char_dir = f"{output_dir}/{char_id:02d}/binFiles"
            os.makedirs(char_dir, exist_ok=True)
            
            # Save palettes
            with open(f"{char_dir}/palette1.bin", 'wb') as f:
                f.write(palette1)
            with open(f"{char_dir}/palette2.bin", 'wb') as f:
                f.write(palette2)
            
            # Save expressions
            for expr in expressions_found:
                with open(f"{char_dir}/{expr['num']:02d}_{expr['name']}_tiles.bin", 'wb') as f:
                    f.write(expr['graphics'])
                
                if expr['oam']:
                    with open(f"{char_dir}/{expr['num']:02d}_{expr['name']}_oam.bin", 'wb') as f:
                        f.write(expr['oam'])
            
            stats['total_chars'] += 1
            stats['total_expressions'] += len(expressions_found)
            
            print(f"Character {char_id:03d}): {len(expressions_found)} expression(s)")
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE!")
    print("="*80)
    print(f"\nStatistics:")
    print(f"  Characters extracted: {stats['total_chars']}")
    print(f"  Total expressions: {stats['total_expressions']}")
    print(f"  DaChan fallback references skipped: {stats['skipped_dachan']}")
    print(f"  (DaChan himself was extracted with all 6 expressions)")
    print(f"\nOutput directory: {output_dir}")

if __name__ == "__main__":
    parse_face_bin('face_Legacy_Claire.bin', 'outputs_Legacy_Claire/characters')

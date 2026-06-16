# Export Feature Documentation

## Overview
The export feature allows users to download generation results as JSON files for analysis, debugging, or record-keeping.

## Usage
1. Generate lyrics using the LyricSmith interface
2. Once generation completes, an "Export" button appears next to the success count
3. Click "Export" to download a JSON file with complete input/output data

## Export Data Structure

### Metadata
- `exportedAt`: ISO timestamp when export was created
- `generatedAt`: ISO timestamp when lyrics were generated
- `messageId`: Unique identifier for the message

### Input (Generation Request)
- `sectionName`: Name of the song section (e.g., "verse1")
- `rhymeScheme`: Rhyme pattern (e.g., "AABB")
- `strictness`: Validation level ("strict", "sung", or "loose")
- `lines`: Array of line specifications
  - `lineNumber`: Position in the section
  - `meaning`: Semantic description
  - `syllables`: Required syllable count
  - `stress`: Stress pattern (if specified)
  - `rhymeLabel`: Rhyme group identifier

### Output (Generation Results)
- `successCount`: Number of successfully generated lines
- `totalLines`: Total number of lines attempted
- `lines`: Array of generation results
  - `lineNumber`: Position in the section
  - `generated`: The generated line text (null if failed)
  - `status`: "PASS" or "FAIL"
  - `attempts`: Number of generation attempts
  - `problems`: Array of validation issues encountered

## Example File
See `EXPORT_EXAMPLE.json` for a sample export file.

## Use Cases
- **Debugging**: Analyze why certain lines failed to generate
- **Research**: Study generation patterns and success rates
- **Backup**: Preserve generation results outside the application
- **Sharing**: Share generation results with collaborators
- **Analysis**: Build datasets for improving the generation system

## File Naming
Export files are named: `lyricsmith-generation-{messageId}-{timestamp}.json`

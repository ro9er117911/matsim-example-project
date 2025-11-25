#!/usr/bin/env python3
"""
XML to GZ Converter Tool for MATSim
Compress XML files to .xml.gz or decompress .xml.gz files to .xml
"""

import gzip
import shutil
import argparse
from pathlib import Path
import sys


def compress_xml_to_gz(xml_path: Path, output_path: Path = None, overwrite: bool = False) -> Path:
    """
    Compress an XML file to .xml.gz format
    
    Args:
        xml_path: Path to the input XML file
        output_path: Optional output path (default: same name with .gz extension)
        overwrite: Whether to overwrite existing output file
        
    Returns:
        Path to the compressed file
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"Input file not found: {xml_path}")
    
    if output_path is None:
        output_path = xml_path.with_suffix(xml_path.suffix + '.gz')
    
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output_path}. Use --overwrite to replace.")
    
    print(f"Compressing: {xml_path} -> {output_path}")
    
    with open(xml_path, 'rb') as f_in:
        with gzip.open(output_path, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Show compression stats
    original_size = xml_path.stat().st_size
    compressed_size = output_path.stat().st_size
    ratio = (1 - compressed_size / original_size) * 100
    print(f"✓ Compressed: {original_size:,} bytes -> {compressed_size:,} bytes ({ratio:.1f}% reduction)")
    
    return output_path


def decompress_gz_to_xml(gz_path: Path, output_path: Path = None, overwrite: bool = False) -> Path:
    """
    Decompress a .gz file to XML format
    
    Args:
        gz_path: Path to the input .gz file
        output_path: Optional output path (default: same name without .gz extension)
        overwrite: Whether to overwrite existing output file
        
    Returns:
        Path to the decompressed file
    """
    if not gz_path.exists():
        raise FileNotFoundError(f"Input file not found: {gz_path}")
    
    if output_path is None:
        if gz_path.suffix == '.gz':
            output_path = gz_path.with_suffix('')
        else:
            output_path = gz_path.parent / (gz_path.stem + '_decompressed.xml')
    
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output_path}. Use --overwrite to replace.")
    
    print(f"Decompressing: {gz_path} -> {output_path}")
    
    with gzip.open(gz_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Show decompression stats
    compressed_size = gz_path.stat().st_size
    decompressed_size = output_path.stat().st_size
    print(f"✓ Decompressed: {compressed_size:,} bytes -> {decompressed_size:,} bytes")
    
    return output_path


def process_directory(input_dir: Path, mode: str, pattern: str = "*.xml", overwrite: bool = False):
    """
    Process all matching files in a directory
    
    Args:
        input_dir: Directory to process
        mode: 'compress' or 'decompress'
        pattern: File pattern to match
        overwrite: Whether to overwrite existing files
    """
    if mode == 'compress':
        files = list(input_dir.glob(pattern))
        if not files:
            print(f"No files matching '{pattern}' found in {input_dir}")
            return
        
        print(f"Found {len(files)} XML file(s) to compress\n")
        for xml_file in files:
            try:
                compress_xml_to_gz(xml_file, overwrite=overwrite)
            except Exception as e:
                print(f"✗ Error processing {xml_file}: {e}")
                
    elif mode == 'decompress':
        gz_pattern = "*.xml.gz" if pattern == "*.xml" else pattern
        files = list(input_dir.glob(gz_pattern))
        if not files:
            print(f"No files matching '{gz_pattern}' found in {input_dir}")
            return
        
        print(f"Found {len(files)} .gz file(s) to decompress\n")
        for gz_file in files:
            try:
                decompress_gz_to_xml(gz_file, overwrite=overwrite)
            except Exception as e:
                print(f"✗ Error processing {gz_file}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert between XML and XML.GZ formats for MATSim",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compress a single XML file
  python xml_gz_converter.py compress input.xml
  
  # Decompress a single GZ file
  python xml_gz_converter.py decompress output_events.xml.gz
  
  # Compress all XML files in output directory
  python xml_gz_converter.py compress output/ --directory
  
  # Decompress all .xml.gz files in a directory
  python xml_gz_converter.py decompress output/ --directory
  
  # Overwrite existing files
  python xml_gz_converter.py compress input.xml --overwrite
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['compress', 'decompress', 'c', 'd'],
        help="Operation mode: compress (c) or decompress (d)"
    )
    
    parser.add_argument(
        'input',
        type=str,
        help="Input file or directory path"
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output file path (for single file mode)"
    )
    
    parser.add_argument(
        '-d', '--directory',
        action='store_true',
        help="Process all files in directory"
    )
    
    parser.add_argument(
        '-p', '--pattern',
        type=str,
        default='*.xml',
        help="File pattern for directory mode (default: *.xml)"
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help="Overwrite existing output files"
    )
    
    args = parser.parse_args()
    
    # Normalize mode
    mode = 'compress' if args.mode in ['compress', 'c'] else 'decompress'
    
    input_path = Path(args.input)
    
    try:
        if args.directory:
            if not input_path.is_dir():
                print(f"Error: {input_path} is not a directory")
                sys.exit(1)
            process_directory(input_path, mode, args.pattern, args.overwrite)
        else:
            if not input_path.is_file():
                print(f"Error: {input_path} is not a file")
                sys.exit(1)
            
            output_path = Path(args.output) if args.output else None
            
            if mode == 'compress':
                compress_xml_to_gz(input_path, output_path, args.overwrite)
            else:
                decompress_gz_to_xml(input_path, output_path, args.overwrite)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

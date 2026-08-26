#!/usr/bin/env python3
from pathlib import Path

p = Path('lib/core/services/native_tool_executor.dart')
text = p.read_text()
old = '''  Future<Map<String, dynamic>> _executeFFmpeg(Map<String, dynamic> args) async {
    final inputPath = args['input_path'] as String?;
    final outputPath = args['output_path'] as String?;
    final operation = args['operation'] as String?;
    final params = args['params'] as Map<String, dynamic>? ?? {};

    if (inputPath == null || outputPath == null || operation == null) {
      throw ArgumentError('Missing required parameters: input_path, output_path, operation');
    }

    // Verify input file exists
    if (!await File(inputPath).exists()) {
      throw ArgumentError('Input file does not exist: $inputPath');
    }

    // Build FFmpeg command based on operation
    // -y flag to auto-overwrite existing files
    String command;
    switch (operation) {
'''
new = '''  Future<Map<String, dynamic>> _executeFFmpeg(Map<String, dynamic> args) async {
    final requestedInputPath = args['input_path'] as String?;
    final inputPaths = (args['input_paths'] as List?)
            ?.map((e) => e.toString())
            .where((e) => e.isNotEmpty)
            .toList() ??
        <String>[];
    final outputPath = args['output_path'] as String?;
    final operation = args['operation'] as String?;
    final params = args['params'] as Map<String, dynamic>? ?? {};
    final primaryInputPath = requestedInputPath ??
        (inputPaths.isNotEmpty ? inputPaths.first : null);

    if (outputPath == null || operation == null || primaryInputPath == null) {
      throw ArgumentError(
          'Missing required parameters: output_path, operation, and input_path or input_paths');
    }
    final inputPath = primaryInputPath;
    final effectiveInputs = inputPaths.isNotEmpty ? inputPaths : <String>[inputPath];

    // Verify every structured input file exists before invoking FFmpegKit.
    for (final path in effectiveInputs) {
      if (!await File(path).exists()) {
        throw ArgumentError('Input file does not exist: $path');
      }
    }

    // Build FFmpeg command based on operation
    // -y flag to auto-overwrite existing files
    String command;
    switch (operation) {
      case 'concat':
        if (effectiveInputs.length < 2) {
          throw ArgumentError('concat requires at least two input_paths');
        }
        final inputs = effectiveInputs.map((p) => '-i "$p"').join(' ');
        var mediaType = (params['media_type'] ?? 'auto').toString().toLowerCase();
        if (mediaType == 'auto') {
          const audioExts = <String>{'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus'};
          final allAudio = effectiveInputs.every((p) {
            final dot = p.lastIndexOf('.');
            return dot >= 0 && audioExts.contains(p.substring(dot).toLowerCase());
          });
          mediaType = allAudio ? 'audio' : 'video';
        }
        if (mediaType == 'audio') {
          final labels = List.generate(effectiveInputs.length, (i) => '[$i:a:0]').join();
          command = '-y $inputs -filter_complex "${labels}concat=n=${effectiveInputs.length}:v=0:a=1[a]" -map "[a]" "$outputPath"';
        } else {
          final labels = List.generate(effectiveInputs.length, (i) => '[$i:v:0][$i:a:0]').join();
          command = '-y $inputs -filter_complex "${labels}concat=n=${effectiveInputs.length}:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac "$outputPath"';
        }
        break;

      case 'mix_audio':
        if (effectiveInputs.length < 2) {
          throw ArgumentError('mix_audio requires at least two input_paths');
        }
        final inputs = effectiveInputs.map((p) => '-i "$p"').join(' ');
        final labels = List.generate(effectiveInputs.length, (i) => '[$i:a:0]').join();
        final durationMode = (params['duration'] ?? 'longest').toString();
        command = '-y $inputs -filter_complex "${labels}amix=inputs=${effectiveInputs.length}:duration=$durationMode:normalize=0[a]" -map "[a]" "$outputPath"';
        break;

      case 'merge_av':
        if (effectiveInputs.length < 2) {
          throw ArgumentError('merge_av requires input_paths=[video, audio]');
        }
        command = '-y -i "${effectiveInputs[0]}" -i "${effectiveInputs[1]}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest "$outputPath"';
        break;
'''
if old not in text:
    raise SystemExit('v7 native anchor missing: _executeFFmpeg preamble')
text = text.replace(old, new, 1)
p.write_text(text)
print('Applied RastaCoder v7 structured FFmpeg patch')

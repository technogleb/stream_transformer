"""This module implements StreamFileMapper class for filtering big files in a stream"""

from pathlib import Path
import os
import multiprocessing
import subprocess
import re


class StreamFileMapper:
    def __init__(self, path, target, chunk_size=1024,
                 n_jobs=1, line_by_line=False, keep_orig_file=True):
        self.path = Path(path)
        self.target = target
        self.chunk_size = chunk_size
        self.n_jobs = n_jobs
        self.line_by_line = line_by_line
        self.keep_orig_file = keep_orig_file

    @property
    def file_size(self):
        stdout = subprocess.check_output(['wc', '-c', self.path])
        pattern = re.compile(b'\d+')
        bytes_len = int(pattern.search(stdout).group())
        return bytes_len

    @property
    def num_lines(self):
        stdout = subprocess.check_output(['wc', '-l', self.path])
        pattern = re.compile(b'\d+')
        num_lines = int(pattern.search(stdout).group())
        return num_lines

    def _read_file_in_stream(self, f):
        while True:
            chunk = next(f, None) if self.line_by_line else f.read(self.chunk_size)
            if not chunk:
                break
            yield chunk

    def _split_file(self):
        split_by = '-l' if self.line_by_line else '-b'
        if self.line_by_line:
            split_size = self.num_lines // self.n_jobs + 1
        else:
            split_size = self.file_size // self.n_jobs + 1

        output_prefix = self.path.parent / ('.' + self.path.stem)

        subprocess.check_call([
            'split',
            '--numeric-suffixes',
            str(split_by),
            str(split_size),
            self.path,
            output_prefix
        ])

        if not self.keep_orig_file:
            subprocess.Popen(['rm', self.path])

        splited_fnames = self.path.parent.glob('.{}*'.format(self.path.stem))

        return splited_fnames

    def _process_chunk(self, chunk):
        return self.target(chunk)

    def _process_file_in_stream(self, f):
        for chunk in self._read_file_in_stream(f):
            yield self._process_chunk(chunk)

    def _open_process_save(self, filename):
        filename_copy = Path(filename.stem + '_processed')
        with open(filename, 'r') as f, open(filename_copy, 'a+') as f_copy:
            for processed_chunk in self._process_file_in_stream(f):
                f_copy.write(processed_chunk)
        return filename_copy

    def _clean_garbage(self):
        for f in self.path.parent.iterdir():
            if re.search('.{}'.format(self.path.stem), str(f)):
                (self.path.parent / f).unlink()

    def map(self):
        splited_fnames = self._split_file()
        with multiprocessing.Pool(self.n_jobs) as P:
            splited_fnames_processed = P.map(self._open_process_save, splited_fnames)

        output_file = self.path.parent / (self.path.stem + '_processed' + self.path.suffix)
        subprocess.check_call(['touch', output_file])

        subprocess.check_call(
            ' '.join(['cat', *map(str, splited_fnames_processed), '>>', str(output_file)]), shell=True)

        self._clean_garbage()


if __name__ == "__main__":
    """Example usage"""

    def mapper_target(x):
        return 'I am replaced string'

    mapper = StreamFileMapper(
        path="../data/file.txt",
        target=mapper_target,
        n_jobs=10,
        line_by_line=True,
        keep_orig_file=False
    )

    mapper.map()

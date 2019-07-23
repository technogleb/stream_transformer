"""This module implements StreamFileMapper class for filtering big files in a stream"""

import os
import multiprocessing
import subprocess
import glob
import re


class StreamFileMapper:
    def __init__(self, path, target, chunk_size=1024,
                 n_jobs=1, line_by_line=False, keep_orig_file=True):
        self.path = path
        self.target = target
        self.chunk_size = chunk_size
        self.n_jobs = n_jobs
        self.line_by_line = line_by_line
        self.f_head, self.f_tail = os.path.split(self.path)
        self.f_body, self.f_ext = os.path.splitext(self.f_tail)
        self.keep_orig_file = keep_orig_file

    @property
    def file_size(self):
        bytes_len = subprocess.check_output(['stat', '--printf="%s"', self.path])
        return int(bytes_len.decode('utf-8')[1:-1])

    @property
    def num_lines(self):
        bytes_len = subprocess.check_output(['wc', '-l', self.path])
        return int(bytes_len.decode('utf-8')[0:-1].split(' ')[0])

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

        output_prefix = os.path.join(self.f_head, '.' + self.f_body)

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

        splited_fnames = glob.glob(os.path.join(self.f_head, '.{}*'.format(self.f_body)))

        return splited_fnames

    def _process_chunk(self, chunk):
        return self.target(chunk)

    def _process_file_in_stream(self, f):
        for chunk in self._read_file_in_stream(f):
            yield self._process_chunk(chunk)

    def _open_process_save(self, filename):
        filename_copy = filename+'_processed'
        with open(filename, 'r') as f, open(filename_copy, 'a+') as f_copy:
            for processed_chunk in self._process_file_in_stream(f):
                f_copy.write(processed_chunk)
        return filename_copy

    def _clean_garbage(self):
        for f in os.listdir(self.f_head):
            if re.search('.{}'.format(self.f_body), f):
                os.remove(os.path.join(self.f_head, f))

    def map(self):
        splited_fnames = self._split_file()
        with multiprocessing.Pool(self.n_jobs) as P:
            splited_fnames_processed = P.map(self._open_process_save, splited_fnames)

        output_file = os.path.join(self.f_head, self.f_body + '_processed' + self.f_ext)
        subprocess.check_call(['touch', output_file])

        subprocess.check_call(
            ' '.join(['cat', *splited_fnames_processed, '>>', output_file]), shell=True)

        self._clean_garbage()


if __name__ == "__main__":
    """Example usage"""
    mapper = StreamFileMapper(
        path="path/to/my/big/file.ext",
        target="my_mapper_funcion",
        n_jobs=10,
        line_by_line=True,
        keep_orig_file=False
    )

    mapper.map()

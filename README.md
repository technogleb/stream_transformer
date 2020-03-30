# stream_transformer

This repository contains file mapper for unix, that can be used as alternative to awk/sed with an ability to use any python function as a mapper.

That can be helpful, if you have a large file not fitting into RAM and any python function for mapping each line or byte chunk. 

It also empowers to use multiprocessing for mapping in parallel.

## Usage.
``` python
from stream_transformer import StreamFileMapper

mapper = StreamFileMapper(
    path="path/to/your/big/file.ext",
    target=your_mapper_function,
    n_jobs=10,
    line_by_line=True,
    keep_orig_file=False
)

mapper.map()
```

* you can use generate_file.sh script to generate large file out of your sample file.txt


import setuptools

setuptools.setup(
    name="svutil",
    version="0.10",
    author="En-Ho Shen",
    author_email="enhoshen@gmail.com",
    url="https://github.com/enhoshen/SVutil",
    packages=setuptools.find_packages(),
    install_requires=[
        "colorama",
        "xlsxwriter",
        "nicotb @ git+https://github.com/johnjohnlin/nicotb",
    ],
    package_dir={"svutil": "svutil"},
    package_data={
        "svutil.gen": ["drawio_block_ex.txt, *.md"],
        "svutil.sim": ["*.md", "mynWave.conf", "mynovas.rc"],
    },
    scripts=["script/Gen.py"],
)

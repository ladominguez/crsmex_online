import setuptools

setuptools.setup(
    name='crsmex-online',
    version='0.0.1',
    author='Luis A. Dominguez',
    author_email='ladominguez@ucla.edu',
    url='https://github.com/ladominguez/',
    description='Looks for repeaters real time.',
    packages=setuptools.find_packages(),
    install_requires=[
        'pandas', 
        'requests-oauthlib',
        'tweepy', 
        'h5py', 
        'tqdm', 
        'numpy', 
        'pygmt',
        ],
    python_requires = ">=3.8"

)

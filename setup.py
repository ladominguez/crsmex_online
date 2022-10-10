import setuptools

setuptools.setup(
	name='crsmex-online',
	version='0.0.1',
	author='Luis A. Dominguez',
	author_email='ladominguez@ucla.edu',
	url='https://github.com/ladominguez/',
	description='Looks for repeaters real time.'
	packages=setuptools.find_packages(),
	install_requires = ['pandas', 'squilte3', 'tweepy', 'h5py', 'tqdm', 'json']

)

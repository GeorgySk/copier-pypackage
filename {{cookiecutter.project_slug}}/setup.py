from pathlib import Path

from setuptools import (find_packages,
                        setup)

import {{cookiecutter.project_slug}}

project_base_url = 'https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/'

setup(name=gon.__name__,
      packages=find_packages(exclude=('tests', 'tests.*')),
      version=gon.__version__,
      description=gon.__doc__,
      long_description=Path('README.md').read_text(encoding='utf-8'),
      long_description_content_type='text/markdown',
      author='{{ cookiecutter.full_name }}',
      author_email='{{ cookiecutter.email }}',
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
      ],
      license='MIT License',
      url=project_base_url,
      download_url=project_base_url + 'archive/master.zip',
      python_requires='>=3.7.0',
      install_requires=Path('requirements.txt').read_text(encoding='utf-8'))

```shell
rm dist/*
python -m build
twine upload -r testpypi dist/*
twine upload -r pypi dist/*
# use __token__ as user and a token API
```
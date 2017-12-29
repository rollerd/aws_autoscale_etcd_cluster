# USAGE

Lambda requires that your function be packaged along with all of its dependencies. For this etcd_lambda script the only outside dependency that we need is 'requests'.

This can be accomplished by telling pip to install requests in the current directory (or a path of your choosing):
```
pip install requests -t ./
```

Next, we need to zip everything up and copy it over to the 
`
../terraform_modules/etcd/lambda/files/ 
`
directory using:
```
zip -r etcdlambda *
```

#### Note:
Our lambda module looks for a file named etcdlambda.zip 

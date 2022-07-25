<div align="center">
    <img src="https://media-exp1.licdn.com/dms/image/C4E1BAQH3ErUUfLXoHQ/company-background_10000/0/1536307975124?e=2159024400&v=beta&t=ZEgfg0K-n-14aYXq8m-aZRprGvwL5HMZF6YMPrUDiQI">
</div>


[![PyPI - Python
Version](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-blue)](https://pypi.org/project/nbox/)
[![Downloads](https://pepy.tech/badge/nbox)](https://pepy.tech/project/nbox)
![GitHub](https://img.shields.io/badge/license-Apache--2.0-blueviolet)

## 🧐 What is Nbox?

`nbox` provides first class support API for all NimbleBox.ai infrastructure (NBX-Build, Jobs, Deploy) and services (NBX-Workspaces) components. Write jobs using `nbox.Operators`

# 🤷Why nimblebox

- Write and execute code in Python
- Document your code that supports mathematical equations
- Create/Upload/Share notebooks
- Import notebooks from your local machine
- Import/Publish notebooks from/to GitHub
- Import external datasets (e.g. from Kaggle)
- Integrate PyTorch, TensorFlow, Keras, OpenCV
- Share your projects
- Collaborate with your team

# 🎚 Features

### Use the hardware you want
<img src="https://nimblebox.ai/_next/image?url=%2F_next%2Fstatic%2Fmedia%2FbuildImg1.c3679150.png&w=3840&q=75" width="700" >

### Secure SSH tunneling
<img src="https://nimblebox.ai/_next/image?url=%2F_next%2Fstatic%2Fmedia%2FbuildImg2.8c393e2c.png&w=3840&q=75" width="700">

### Work with your favourite IDE 
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Jupyter_logo.svg/1200px-Jupyter_logo.svg.png" width="70"><img src="https://code.visualstudio.com/assets/branding/app-icon.png" width="70">
<img src="https://avatars.githubusercontent.com/u/22800682?s=280&v=4" width="70">

<img src="https://nimblebox.ai/_next/image?url=%2F_next%2Fstatic%2Fmedia%2FbuildImg3.d25060b5.png&w=3840&q=75" width="700">

## ⏲ Schedule jobs
### Seamless Integreation
<img src="https://nimblebox.ai/_next/image?url=%2F_next%2Fstatic%2Fmedia%2FjobsImg1.b064d453.png&w=3840&q=75" width="700">

## 🚀 Deploy with ease
<img src="https://nimblebox.ai/_next/image?url=%2F_next%2Fstatic%2Fmedia%2FdeployImg1.e4557546.png&w=3840&q=75" width="700">

# 🏁 Get Started


**Install the package from pipy:**

```pip install nbox```


For convinience you should add nbox to your path by setting up an alias. Throughout the rest of the documentation we will be using nbx as the CLI:

```# go to your .bashrc or .zshrc and add
alias nbx="python3 -m nbox"
```



When loading nbox for the first time, it will prompt you the username and password and create a secrets file at ```~/.nbx/secrets.json. ``` This file then contains all the information that you don’t have to fetch manually again.


## APIs

Our APIs are deep, user functions are kept to minimum and most relavant. This documentation contains the full spec of everything, but here’s all the APIs you need to know:

```
nbox
├── Model          # Framework agnostic Model
│   ├── __call__
│   ├── deploy
│   ├── train_on_instance (WIP)
│   └── train_on_jobs (WIP)
├── Operators      # How jobs are combinations of operators
│   ├── __call__
│   └── deploy
├── Jobs           # For controlling all your jobs
│   ├── logs       # stream logs right on your terminal
│   └── trigger    # manually trigger a job
└── Instance
   ├── __call__    # Run any command on the instance
   └── mv (WIP)    # Move files to and from NBX-Build
```
### Deploy your machine learning or statistical models:

```python
from nbox import Model
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# define your pre and post processing functions
def pre(x: Dict):
  return AutoTokenizer(**x)

# load your classifier with functions
model = AutoModelForSequenceClassification.from_pretrained("distill-bert")
classifier = Model(model, pre = pre)

# call your model
classifier(f"Is this a good picture?")

# get full control on exporting it
spec = classifier.torch_to_onnx(
  TorchToOnnx(...)
)

# confident? deploy it your cloud
url, key = classifier.deploy(
  spec, deployment_id_or_name = "classification"
)

# use it anywhere
pred = requests.post(
  url,
  json = {
    "text": f"Is this a good picture?"
  },
  header = {"Authorization": f"Bearer {key}"}
).json()
```
# 🛟 How to get help?

Join our [discord](https://discord.gg/qYZHxMaCsE) and someone from our community or engineering team will respond!

## 🔖Read our [Blog](https://nimblebox.ai/blog).


# 🧩 License

The code in thist repo is licensed as [Apache License 2.0](./LICENSE). Please check for individual repositories for licenses.

# Instructions on Using the DML Library

1. Install the DML Library (must be using Python 2.7).
```
npm install dataagora-dml
```

2. Import the library.
```
const dataagora = require('dataagora-dml');
```

3. Set the `repo_id`. This should come from your newly created repo.
```
repo_id = sample_repo_id;
```

4. Get your data. Must be of type `Tensor2D`.
```
data = getData();
```

5. Bootstrap the library with your `repo_id`. Store the data with a repo name and wait for incoming library requests to train on your data!
```
dataagora.bootstrap_and_store(repo_id, data);
```

You can see an example in `test/sample.js`.

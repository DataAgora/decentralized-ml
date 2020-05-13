import React from 'react';
import Reflux from 'reflux';
import RepoStatus from './repoStatus';

class RepoMetadata extends Reflux.Component {

    constructor(props) {
        super(props);

        this.repoData = this.props.repoData;
        this.copyRepoIDToClipboard = this.copyRepoIDToClipboard.bind(this);
    }

    copyRepoIDToClipboard() {
        // const { match: { params } } = this.props;
        // const repoId = params.repoId;
        var dummy = document.createElement("textarea");
        document.body.appendChild(dummy);
        dummy.value = this.repoData.Id;
        dummy.select();
        document.execCommand("copy");
        document.body.removeChild(dummy);
    }

    render() {
        if (!this.repoData.isDemo) {
            return (
                <div className="row">
                    <div className="col-1"></div>
                    <div className="col-3">
                    <h3>{this.repoData.Name}</h3>
                    <p>{this.repoData.Description}</p>
                    </div>
                    <div className="col-5 padding">
                        <h6> <b>REPO ID:  <span className="text-success">{ this.repoData.Id }</span></b>   <button class="btn btn-xs btn-dark copy" onClick={this.copyRepoIDToClipboard}>Copy to Clipboard</button></h6>  
                    </div>
                    <div className="col-2 text-right">
                    <RepoStatus repoId={this.repoData.Id} isDashboard={false}/>
                    </div>
              </div>
            )
            return 
        } else {
            return (
                <div className="row">
                    <div className="col-1"></div>
                    <div className="col-8">
                    <h3>{this.repoData.Name}</h3>
                    <p>{this.repoData.Description}</p>
                    </div>
                    <div className="col-2 text-right">
                    <RepoStatus repoId={this.repoData.Id} isDashboard={false}/>
                    </div>
              </div>
            )
        }
    }
}

export default RepoMetadata;

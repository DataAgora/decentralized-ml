import React from 'react';
import Reflux from 'reflux';

import CoordinatorStore from './../../stores/CoordinatorStore';
import CoordinatorActions from './../../actions/CoordinatorActions';
import RepoDataActions from './../../actions/RepoDataActions';

class RepoStatus extends Reflux.Component {

    constructor(props) {
        super(props);
        this.store = CoordinatorStore;

        this.repoId = this.props.repoId
        this.isDashboard = this.props.isDashboard;
        this.resetState = this.resetState.bind(this);
        this.deleteRepo = this.deleteRepo.bind(this);
        this.launchExplora = this.launchExplora.bind(this);
        this.exploraURL = "http://" + this.repoId + ".explora.discreetai.com"
    }

    componentDidMount() {
        CoordinatorActions.fetchCoordinatorStatus(this.props.repoId);
    }

    resetState() {
        RepoDataActions.resetState(this.repoId);
    }

    deleteRepo() {
        var response = window.confirm("Are you sure you want to delete your repo?");

        if (response) {
            RepoDataActions.deleteRepo(this.repoId);
        }
    }

    launchExplora() {
        var win = window.open(this.exploraURL, '_blank');
        win.focus();
    }

    render() {
        const status = this.state.coordinatorStatuses[this.props.repoId];

        if (this.isDashboard) {
            switch (status) {
                case "ERROR": return <span className="badge badge-pill badge-danger">Error</span>;
                case "SHUTTING DOWN": return <span className="badge badge-pill badge-danger">Shutting down..</span>;
                case "DEPLOYING": return <span className="badge badge-pill badge-warning">Deploying...</span>;
                case "ACTIVE": return <span className="badge badge-pill badge-success">Active</span>;
                case "AVAILABLE": return <span className="badge badge-pill badge-secondary">Idle</span>;
                default: return <span className="badge badge-pill badge-dark">...</span>;
            }
        } else {
            switch (status) {
                case "ERROR": return <p><span className="badge badge-pill badge-danger">Error</span><p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark" disabled ><b>Reset</b></button></p><p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p></p>;
                case "SHUTTING DOWN": return <p><span className="badge badge-pill badge-danger">Shutting down..</span><p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark" disabled ><b>Reset</b></button></p><p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p></p>;
                case "DEPLOYING": return <p><span className="badge badge-pill badge-warning">Deploying...</span><p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark" disabled ><b>Reset</b></button></p><p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p></p>;
                case "ACTIVE": return <p><span className="badge badge-pill badge-success">Active</span><p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark"><b>Reset</b></button></p><p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p></p>;
                case "AVAILABLE": return <p><span className="badge badge-pill badge-secondary">Idle</span><p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark"><b>Reset</b></button></p><p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p></p>;
                default: return <p><span className="badge badge-pill badge-dark">...</span><p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark" disabled ><b>Reset</b></button></p><p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p></p>;
            }
        }
        
    }
}

export default RepoStatus;

import React from 'react';
import Reflux from 'reflux';
import ReactDOM from 'react-dom';
import { Link } from 'react-router-dom';

import RepoDataStore from './../stores/RepoDataStore';
import RepoDataActions from './../actions/RepoDataActions';

import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';


class NewRepo extends Reflux.Component {

  constructor(props) {
    super(props);
    this.store = RepoDataStore;
    this.checkRepoName = this.checkRepoName.bind(this);
  }

  componentDidMount() {
    RepoDataActions.fetchReposRemaining();
  }

  checkRepoName() {
    let repoName = document.getElementById('repoNameInput')
    let cleanRepoName = repoName.value.replace(/[^a-zA-Z0-9-]/g,'-');
    if (repoName.value != cleanRepoName) {
      repoName.setCustomValidity("Repo name must only contain letters, numbers or hyphens!")
    }
  }

  _handleSubmit(event) {
    event.preventDefault();

    let form = document.getElementById('newRepoForm');

    if (form.reportValidity()) {
      let repoName = ReactDOM.findDOMNode(this.refs.repoName).value.replace(/[^a-zA-Z0-9-]/g,'-');
      RepoDataActions.createNewRepo(
        repoName,
        ReactDOM.findDOMNode(this.refs.repoDescription).value
      );
    }
  }

  _handleContinue() {
    RepoDataActions.resetState();
    this.props.history.push("/repo/" + this.state.creationState.repoId);
  }

  render() {
    // Get number of repos left.
    if (this.state.creationState.loading === true) {
      return (
        <div className="text-center text-secondary">
          <FontAwesomeIcon icon="sync" size="lg" spin />
        </div>
      );
    }

    if (this.state.creationState.created) {
      this._handleContinue()
    }

    let reposLeft = this.state.creationState.reposRemaining;
    if (!reposLeft) {
      return (
        <div className="text-center">
          <h3>Sorry, but you have no more repos left.</h3>
          <p className="mt-4">If you want to upgrade your account to support more repos, <a href="mailto:neelesh.dodda@discreetai.com?subject=Upgrade Account&body=I would like to upgrade my account!">please email us</a>.</p>
          <p className="mt-3"><Link to="/">Back to dashboard</Link></p>
        </div>
      );
    } else {
      var waitMessage = "";
      var createRepoButton = (<button type="submit" className="btn btn-lg btn-primary" onClick={this._handleSubmit.bind(this)}>Create Repo</button>);

      if (this.state.creationState.creating) {
        createRepoButton = (<button type="submit" className="btn btn-lg btn-primary" onClick={this._handleSubmit.bind(this)} disabled>Create Repo</button>);
        waitMessage = (<p id="wait" className="mt-3"><b>Please wait...</b></p>);
      }

      return (
        <div className="row">
          <div className="col-4"></div>
          <div className="col-4">
            <h3>Create a new repo</h3>
            <p className="mt-3">A <b>repo</b> is a link to a network of devices, history of training, and resulting models.</p>
            <p className="mt-3">Create a new repository to start doing private federated learning. Repos are private by default.</p>
            <form id="newRepoForm" className="mt-4">
              <div className="form-group">
               <label htmlFor="repoNameInput">Repo name</label>
               <input type="text" className="form-control" id="repoNameInput" ref="repoName" aria-describedby="repoName" placeholder="awesome-dml-experiment" maxLength="20" onInput={this.checkRepoName} required/>
               <small id="repoNameHelp" className="form-text text-muted">Use a repo name you haven't used yet. Make it catchy.</small>
              </div>
              <div className="form-group">
               <label htmlFor="repoDescriptionInput">Brief description</label>
               <input type="text" className="form-control" id="repoDescriptionInput" ref="repoDescription" placeholder="To do magic on users' data without even seeing it." maxLength="80" required/>
               <small id="repoDescriptionHelp" className="form-text text-muted">Anything will do. Use this to remember what a repo is about.</small>
              </div>
              <div className="text-center mt-5">
                { createRepoButton }
                { waitMessage }
              </div>
            </form>
          </div>
        </div>
      );
    }
  }
}

export default NewRepo;

import React from 'react';
import ReactDOM from 'react-dom';
import Reflux from 'reflux';

import NotFoundPage from './notFoundPage';
import RepoStatus from './repo/repoStatus';
import LaunchStep from './repo/launchStep';
import RepoMetadata from './repo/repoMetadata';
import RepoLogs from './repo/repoLogs';
import RepoModels from './repo/repoModels';
import { Link } from 'react-router-dom';

import RepoDataStore from './../stores/RepoDataStore';
import RepoDataActions from './../actions/RepoDataActions';

import RepoLogsStore from './../stores/RepoLogsStore';
import RepoLogsActions from './../actions/RepoLogsActions';

import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';

import Endpoints from './../constants/endpoints.js';
import AuthStore from './../stores/AuthStore';

import trackRepoStatus from "./../utils/updateStatus";


class Repo extends Reflux.Component {
  constructor(props) {
    super(props);
    this.stores = [RepoDataStore, RepoLogsStore];

    const { match: { params } } = this.props;
    this.repoId = params.repoId;
  }

  componentDidMount() {
    // const { match: { params } } = this.props;
    // const repoId = params.repoId;
    RepoDataActions.fetchRepoData(this.repoId);
    RepoLogsActions.fetchRepoLogs(this.repoId);
    trackRepoStatus(this.repoId, false)
  }

  render() {
    let logs = this.state.repoLogs[this.repoId]

    if (this.state.loading === true) {
      return (
        <div className="text-center text-secondary">
          <FontAwesomeIcon icon="sync" size="lg" spin />
        </div>
      );
    }

    if (!this.state.repoWasFound) {
      return <NotFoundPage />
    }
    
    return (
      <div className="pb-5">
        <RepoMetadata repoData={this.state.repoData}/>
       
        <div className="row">
        <div className="col-1"></div>
          <div className="col-8">

            <p id="bigo">
              <br></br><br></br>
              <h1>Getting Started</h1>
              <br></br>
              To start your training session, complete the following steps once the cloud node status is <b>Idle</b>.
              <br></br><br></br>
              <ol>
                <LaunchStep repoId={this.state.repoData.Id} apiKey={this.state.repoData.ApiKey} isDemo={this.state.repoData.IsDemo} ExploraUrl={this.state.repoData.ExploraUrl}/>
                <br></br>
                <li>Run the cells to begin training with the sample model!</li>
              </ol>
              </p>
          </div>
        </div>

        <RepoModels logs={logs} repoId={this.state.repoData.Id} />

      </div>
    )
  }
}

export default Repo;

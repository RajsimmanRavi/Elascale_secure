# Autoscaler
The core Autoscaling engine for Elascale Platform. This is deployed on the Swarm Master Host OS. Previous version used to be deployed as Docker service. But, we found that it adds major overhead on development, deployment, latency issues etc. Hence, depracating the development of utilizing Docker services/containers to deploy Autoscaler and UI. 

# UI
The UI showcases some Kibana dashboards and can be used for configuration purposes as well. 

# Execution
You can run the application on a tmux/screen session using the following command:

```tmux new -d -s manager 'sudo python3 -m autoscaler.manager.main'```

You can run the UI on a tmux/screen session using the following command:

```tmux new -d -s ui 'sudo python3 -m autoscaler.ui.main'```

Note: Make sure you change your folder to: Elascale_secure (eg. /home/ubuntu/Elascale_secure) 

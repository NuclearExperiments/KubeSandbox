# Notes
## Rancher
Rancher is an open-source container management platform designed to simplify Kubernetes operations. It is designed to be deployed in production clusters to provide additional features over Kubernetes but its easy to use UI could be used to explore and learn about Kubernetes ecosystem. KubeSandbox will deploy Rancher to the cluster using a Helm chart. The services will be created but it can take some time for them to start running. You can check if the service is up by running the following on the terminal:
```shell
kubectl get pods -n cattle-system
```
### Links
- [What is Rancher?](https://www.rancher.com/)
- [Installation Details](https://ranchermanager.docs.rancher.com/getting-started/installation-and-upgrade/install-upgrade-on-a-kubernetes-cluster)



# Resources
| Name | Type | Path | Details | References |
| --- | --- | --- | --- | --- |
| K3D Config | YAML file | k3d-config-1718476195.yaml | File containing the configuration for recreating the current K3D cluster. This cluster will not contain the installed tools or packages. | https://k3d.io/v5.6.3/usage/configfile/ |
| Rancher URL | URL | http://rancher.localhost | URL to access Rancher Dashboard | - |
| Cluster Report | Markdown file | report (0).md | A report containing all the details about the created cluster | - |

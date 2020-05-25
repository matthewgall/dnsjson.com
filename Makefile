export NAME?=dnsjson
export NAMESPACE?=dnsjson
export IMAGE?=matthewgall/dnsjson.com
export COLO:=$(shell kubectx -c)

.PHONY: apply
apply:
	@cat k8s.yml | envsubst | kubectl apply -n ${NAMESPACE} -f -

.PHONY: delete
delete:
	@cat k8s.yml | envsubst | kubectl delete -n ${NAMESPACE} -f -

.PHONY: deploy
deploy:
	kubectl rollout restart deployment/${NAME} -n ${NAMESPACE} && kubectl rollout status deployment/${NAME} -n ${NAMESPACE}
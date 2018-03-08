FROM aem-base

WORKDIR /opt/cq

ADD ./publisher/postInstallHook.py /opt/cq/postInstallHook.py
ADD ./publisher/packages/*.zip /opt/cq/packages/

RUN python aemInstaller.py -i AEM_6.3_Quickstart.jar -r publish -p 4503

EXPOSE 4503
CMD /opt/cq/crx-quickstart/bin/quickstart
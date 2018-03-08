FROM aem-base

WORKDIR /opt/cq

ADD ./author/postInstallHook.py /opt/cq/postInstallHook.py
ADD ./author/packages/*.zip /opt/cq/packages/

RUN python aemInstaller.py -i AEM_6.3_Quickstart.jar -r author -p 4502

EXPOSE 4502
CMD /opt/cq/crx-quickstart/bin/quickstart
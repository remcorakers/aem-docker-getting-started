FROM aem-base

WORKDIR /opt/aem

COPY ./publisher/postInstallHook.py /opt/aem/postInstallHook.py
COPY ./publisher/packages/* /opt/aem/packages/

RUN python aemInstaller.py -i AEM_6.2_Quickstart.jar -r publish -p 4503

EXPOSE 4503
CMD java -Xms4096m -Xmx4096m -Djava.awt.headless=true -jar AEM_6.2_Quickstart.jar -p 4503 -debug 30304 -r publish -v
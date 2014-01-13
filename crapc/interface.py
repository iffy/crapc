from zope.interface import Interface


class IRunner(Interface):


    def runProcedure(self, request):
        """
        Run a procedure.
        """


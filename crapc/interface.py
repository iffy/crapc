from zope.interface import Interface


class ISystem(Interface):


    def runProcedure(request):
        """
        Run a procedure.
        """


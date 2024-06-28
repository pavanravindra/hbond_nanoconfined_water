from ase.calculators.calculator import Calculator, all_changes
from copy import deepcopy
import numpy as np

def ConfiningPotentialMorseEnergetics(D0, z0, a, mask, positions):
    """
    Outputs the energy and forces due to confinment using
    a Morse potential
    """

    exp_term =  np.exp(-a * (positions - z0)) 
    energy = np.sum((D0 * ((1.0 - exp_term)**2 - 1.0)) * mask)
    force = -2.0 * a * D0 * exp_term * (1.0 - exp_term) * mask
    
    # print(exp_term.shape)
    # print(positions.shape)
    # print(exp_term)
    # print(mask[:,2])
    # print ("positions->", (positions))

    return energy, force

class ConfiningPotentialMorseCalculator(Calculator):
    """Wrapper class to implement a confining Morse potential
       as an interatomic potential in ASE

    Parameters
    ----------
    D0 : float
        the dissociation constant of the potential
    z0 : float
        the equilibrium distance
    """

    implemented_properties = ["energy", "forces", "stress"]
    "Properties calculator can handle (energy, forces, ...)"

    default_parameters = {}
    "Default parameters"

    nolabel = True

    def __init__(self, D0, z0, a, w=5, **kwargs):
        super(ConfiningPotentialMorseCalculator, self).__init__(**kwargs)
        self.D0 = D0
        self.z0 = z0
        self.a = a
        self.w = w
        self.kwargs = kwargs

    def calculate(
        self, atoms=None, properties=["energy", "forces", "stress"], system_changes=all_changes
    ):
        Calculator.calculate(self, atoms, properties, system_changes)

        mask = np.asarray([[0.0, 0.0, float(s == 'O')] for s in atoms.get_chemical_symbols()])

        wall1 = atoms.positions * 0.0
        wall2 = atoms.positions * 0.0
        wall2[:,2] = self.w

        energy1s, force1s, energy2s, force2s = [], [], [], []

        for i in range(len(self.D0)):
            energy1, forces1 = ConfiningPotentialMorseEnergetics(self.D0[i], self.z0[i], self.a[i], mask, atoms.positions - wall1)
            energy2, forces2 = ConfiningPotentialMorseEnergetics(self.D0[i], self.z0[i], self.a[i], mask, wall2 - atoms.positions)
            energy1s.append(energy1)
            force1s.append(forces1)
            energy2s.append(energy2)
            force2s.append(forces2)
       
        self.results["energy"] = np.average(energy1s) + np.average(energy2s)
        self.results["free_energy"] = np.average(energy1s) + np.average(energy2s)
        self.results["forces"] = np.average(force1s, axis=0) - np.average(force2s, axis=0)
        self.results["stress"] = np.zeros(6)


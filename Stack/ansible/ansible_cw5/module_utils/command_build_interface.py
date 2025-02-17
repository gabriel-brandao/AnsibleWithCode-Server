class CommandBuildInterface:
    def __init__(self, hostname):
        self.hostname = hostname
        self.status = []  # Flag para rastrear erros e mensagens

    def atualiza_status(self, hostname, port, erro, msg, only_verbose=True):
        """Atualiza o status com erro e mensagem."""
        self.status.append({"saida": erro, "msgs":f"[{hostname}] p.{port} => {msg}", "verbose": only_verbose})    
     
    @staticmethod
    def gera_vlan_commands(hostname, port, type_if, vlan, atualiza_status):
        comando = []
        
        match type_if:
            case "access":
                comando.append("undo voice vlan enable")
                comando.append("port link-type access")
                if not vlan:
                    comando.append("port access vlan 1")
                    atualiza_status(hostname, port, "warn", "VLAN não informada - definido para VLAN 1", True)
                elif len(vlan) > 1:
                        comando.append(f"port access vlan {vlan[0]}")
                        atualiza_status(hostname, port,"warn", f"Mais de uma VLAN em porta access - definido vlan {vlan[0]}", False)
                else: #1 vlan:
                    comando.append(f"port access vlan {vlan[0]}")
                                    
            case "trunk":
                comando.append("port link-type trunk")
                if not vlan:
                    comando.append(f"port trunk permit vlan 1")
                    atualiza_status(hostname, port,"warn", "sem vlan informada, permitido apenas VLAN 1", True)
                else:
                    allow_ids = " ".join(str(id) for id in vlan if id > 0)
                    undo_ids = " ".join(str(abs(id)) for id in vlan if id < 0)

                    if allow_ids:
                        comando.append(f"port trunk permit vlan {allow_ids}")
                    if undo_ids:
                        comando.append(f"undo port trunk permit vlan {undo_ids}")
                        
        return comando

    @staticmethod
    def gera_pvid_commands(hostname, port,type_if, vlan, pvid, atualiza_status):
        comando = []

        match type_if:
            case "access":
                if vlan and pvid not in vlan:
                    atualiza_status(hostname, port, "fail", "PVID não corresponde a vlan passada")

            case "trunk":
                if pvid is not None:
                    if pvid == 1:
                        atualiza_status(hostname, port, "warn", "PVID será definido para VLAN 1", False)	
                        comando.append(f"port trunk pvid vlan 1")	
                    elif pvid > 1 and pvid not in vlan:
                        atualiza_status(hostname, port, "warn", f"PVID definido em {pvid} mas, não definido na lista de vlan !!", False)
                        comando.append(f"port trunk pvid vlan {pvid}")
                    else:
                        comando.append(f"port trunk pvid vlan {pvid}")
        return comando
                        
    @staticmethod
    def gera_voice_commands(hostname, port, type_if, voice, atualiza_status):
        comando = []
        #caso voice seja vazio ou zero, nada é feito
        match type_if:
            case "trunk":
                if voice is not None:
                    if voice > 0:
                        comando.append(f"voice vlan {voice} enable")
                    else:
                        comando.append(f"undo voice vlan enable")
            case "access": #se porta em access já foi removido o voice
                if voice is not None and voice > 0:
                    # colicitação para add voice em porta access
                     atualiza_status(hostname, port, "fail", "Porta access não pode ser voice-vlan")
        return comando 
    
    @staticmethod
    def gera_description_commands(description):
        comando = []
        if description is not None:
            comando.append(f"description {description}")
        return comando
    
    @staticmethod
    def gera_dhcpSnoop_commands(dhcp_snoop):   
        if dhcp_snoop is not None:
            return ["dhcp-snooping trust"] if dhcp_snoop else ["undo dhcp-snoopong trust"]
        
        return []
    
    @staticmethod
    def gera_stp_commands(stp):
        if stp is not None:
            return [f"stp {stp}"] if stp != "edged" else ["stp edged-port enable"]
        return []
        

    def MontaComando(self, interface_config):

        comando = [
            f"interface GigabitEthernet 1/0/{interface_config['port']}"
        ]
        
        #extende evita lista dentro de lista
        comando.extend(self.gera_description_commands(interface_config['description']))
        comando.extend(self.gera_vlan_commands(self.hostname, interface_config['port'], interface_config['type'], interface_config['vlan'], self.atualiza_status))
        comando.extend(self.gera_pvid_commands(self.hostname, interface_config['port'], interface_config['type'], interface_config['vlan'], interface_config['pvid'], self.atualiza_status))
        comando.extend(self.gera_voice_commands(self.hostname, interface_config['port'], interface_config['type'], interface_config['voice'], self.atualiza_status))
        comando.extend(self.gera_dhcpSnoop_commands(interface_config['dhcp_snoop']))
        comando.extend(self.gera_stp_commands(interface_config['stp']))

        return comando, self.status


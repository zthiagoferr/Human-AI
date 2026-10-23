import { Injectable } from '@angular/core';
import {
  User,
  browserLocalPersistence,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendPasswordResetEmail,
  setPersistence,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
} from 'firebase/auth';

import { obterAuth } from './firebase-app';
import { UsuarioFirebase } from './firebase-auth.models';

@Injectable({ providedIn: 'root' })
export class FirebaseAuthGateway {
  private mapear(usuario: User | null): UsuarioFirebase | null {
    if (!usuario) {
      return null;
    }
    return {
      uid: usuario.uid,
      email: usuario.email,
      nome: usuario.displayName,
    };
  }

  configurarPersistencia(): Promise<void> {
    return setPersistence(obterAuth(), browserLocalPersistence);
  }

  async aguardarPronto(): Promise<UsuarioFirebase | null> {
    await obterAuth().authStateReady();
    return this.mapear(obterAuth().currentUser);
  }

  observar(callback: (usuario: UsuarioFirebase | null) => void): () => void {
    return onAuthStateChanged(obterAuth(), (usuario) =>
      callback(this.mapear(usuario)),
    );
  }

  async entrar(email: string, senha: string): Promise<UsuarioFirebase> {
    const credencial = await signInWithEmailAndPassword(
      obterAuth(),
      email,
      senha,
    );
    return this.mapear(credencial.user) as UsuarioFirebase;
  }

  async criar(
    email: string,
    senha: string,
    nome: string,
  ): Promise<UsuarioFirebase> {
    const credencial = await createUserWithEmailAndPassword(
      obterAuth(),
      email,
      senha,
    );
    await updateProfile(credencial.user, { displayName: nome });
    return this.mapear(credencial.user) as UsuarioFirebase;
  }

  async sair(): Promise<void> {
    await signOut(obterAuth());
  }

  async recuperarSenha(email: string): Promise<void> {
    await sendPasswordResetEmail(obterAuth(), email);
  }

  async token(forcar = false): Promise<string | null> {
    const usuario = obterAuth().currentUser;
    return usuario ? usuario.getIdToken(forcar) : null;
  }

  usuarioAtual(): UsuarioFirebase | null {
    return this.mapear(obterAuth().currentUser);
  }
}

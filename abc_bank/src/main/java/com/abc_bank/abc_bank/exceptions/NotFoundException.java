package com.abc_bank.abc_bank.exceptions;



public class NotFoundException extends RuntimeException{
   public NotFoundException(String error){
       super(error);
   }
}

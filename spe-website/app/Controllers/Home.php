<?php

namespace App\Controllers;

class Home extends BaseController
{
    public function index(): string
    {
        $data = [
            'title'     => 'SPE ITS Student Chapter',
            'activeNav' => 'home',
        ];

        return view('home', $data);
    }
}
